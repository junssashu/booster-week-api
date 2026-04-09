import logging
import math
import os
import subprocess
import tempfile
import threading
from datetime import date, timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample
from rest_framework import serializers as drf_serializers

from apps.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from apps.core.throttles import PaymentThrottle
from apps.programs.models import Program

from .models import Enrollment, Payment, PromoCode, PromoCodeRedemption
from .serializers import (
    EnrollmentCreateSerializer,
    EnrollmentDetailSerializer,
    EnrollmentListSerializer,
    PaymentHistorySerializer,
    PaymentInitiateSerializer,
    PaymentSerializer,
    PaymentStatusSerializer,
    PromoCodeSerializer,
    PromoCodeValidateSerializer,
)
from .services import MoneyFusionError, MoneyFusionService

logger = logging.getLogger(__name__)


def _cleanup_enrollment_progress(user, program):
    """Remove all progress data for a user+program when enrollment is cancelled/deleted.

    Cleans up: StepProgress, AssetCompletion, QCMAttempt, FormSubmission,
    and PdcAcceptance for all steps/assets in the program.
    """
    from apps.progress.models import StepProgress, AssetCompletion, QCMAttempt, FormSubmission
    from apps.programs.models import Step, Asset, PriseDeContact

    steps = Step.objects.filter(degree__program=program)
    assets = Asset.objects.filter(step__degree__program=program)
    pdcs = PriseDeContact.objects.filter(
        models.Q(program=program) | models.Q(degree__program=program) | models.Q(step__degree__program=program)
    )

    StepProgress.objects.filter(user=user, step__in=steps).delete()
    AssetCompletion.objects.filter(user=user, asset__in=assets).delete()
    QCMAttempt.objects.filter(user=user, asset__in=assets).delete()
    FormSubmission.objects.filter(user=user, asset__in=assets).delete()

    # Clean PDC acceptances
    from apps.progress.models import PriseDeContactAcceptance
    PriseDeContactAcceptance.objects.filter(user=user, prise_de_contact__in=pdcs).delete()

    logger.info('Cleaned up progress data for user=%s, program=%s', user.id, program.id)


def _complete_payment(payment_id):
    """Atomically complete a payment and update its enrollment.

    Uses select_for_update() to prevent race conditions between
    webhook and verify endpoints processing the same payment.

    Returns the updated payment, or None if already completed (idempotent).
    """
    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(id=payment_id)

        # Idempotency: already completed
        if payment.status == 'completed':
            return None

        payment.status = 'completed'
        payment.save()

        enrollment = Enrollment.objects.select_for_update().get(id=payment.enrollment_id)
        enrollment.amount_paid += payment.amount
        if enrollment.amount_paid >= enrollment.total_amount:
            enrollment.payment_status = 'completed'
        elif enrollment.amount_paid > 0:
            enrollment.payment_status = 'partial'
        enrollment.save()

        # Initialize progress on first payment (non-critical — don't block payment)
        try:
            _initialize_progress(enrollment)
        except Exception:
            logger.exception('Failed to init progress for enrollment %s (payment still completed)', enrollment.id)

        return payment


def _initialize_progress(enrollment):
    """Initialize step_progress for the program on first payment."""
    from apps.progress.models import StepProgress

    # Only initialize if no progress exists yet
    existing = StepProgress.objects.filter(
        user=enrollment.user,
        program=enrollment.program,
    ).exists()
    if existing:
        return

    degrees = enrollment.program.degrees.all().order_by('order_index')
    first_step_set = False

    for degree in degrees:
        if not enrollment.can_access_degree(degree):
            continue
        steps = degree.steps.all().order_by('order_index')
        for step_obj in steps:
            step_status = 'locked'
            if not first_step_set:
                step_status = 'available'
                first_step_set = True

            StepProgress.objects.get_or_create(
                user=enrollment.user,
                step=step_obj,
                defaults={
                    'program': enrollment.program,
                    'status': step_status,
                }
            )


# -- Reusable inline response schemas ----------------------------------------

_ErrorDetailSchema = inline_serializer(
    name='ErrorDetail',
    fields={
        'field': drf_serializers.CharField(),
        'message': drf_serializers.CharField(),
    },
)

_ErrorResponseSchema = inline_serializer(
    name='ErrorResponse',
    fields={
        'error': inline_serializer(
            name='ErrorBody',
            fields={
                'code': drf_serializers.CharField(),
                'message': drf_serializers.CharField(),
                'details': drf_serializers.ListField(
                    child=_ErrorDetailSchema, required=False,
                ),
            },
        ),
    },
)

_EnrollmentListResponseSchema = inline_serializer(
    name='EnrollmentListResponse',
    fields={
        'data': EnrollmentListSerializer(many=True),
    },
)

_EnrollmentCreateResponseSchema = inline_serializer(
    name='EnrollmentCreateResponse',
    fields={
        'data': inline_serializer(
            name='EnrollmentCreateData',
            fields={
                'id': drf_serializers.CharField(),
                'programId': drf_serializers.CharField(),
                'userId': drf_serializers.CharField(),
                'paymentType': drf_serializers.ChoiceField(choices=['full', 'installment']),
                'paymentStatus': drf_serializers.CharField(),
                'amountPaid': drf_serializers.IntegerField(),
                'totalAmount': drf_serializers.IntegerField(),
                'installmentAmount': drf_serializers.IntegerField(allow_null=True),
                'enrollmentDate': drf_serializers.DateTimeField(),
                'payments': PaymentSerializer(many=True),
            },
        ),
    },
)

_PaymentInitiateResponseSchema = inline_serializer(
    name='PaymentInitiateResponse',
    fields={
        'data': inline_serializer(
            name='PaymentInitiateData',
            fields={
                'paymentId': drf_serializers.CharField(),
                'transactionId': drf_serializers.CharField(),
                'status': drf_serializers.CharField(),
                'message': drf_serializers.CharField(),
                'expiresAt': drf_serializers.DateTimeField(),
                'paymentUrl': drf_serializers.URLField(required=False),
            },
        ),
    },
)

_PaymentListResponseSchema = inline_serializer(
    name='PaymentListResponse',
    fields={
        'data': PaymentSerializer(many=True),
    },
)

_WebhookReceivedSchema = inline_serializer(
    name='WebhookReceived',
    fields={
        'received': drf_serializers.BooleanField(),
    },
)

_DevSimulateResponseSchema = inline_serializer(
    name='DevSimulateResponse',
    fields={
        'data': inline_serializer(
            name='DevSimulateData',
            fields={
                'paymentId': drf_serializers.CharField(),
                'status': drf_serializers.CharField(),
                'enrollmentPaymentStatus': drf_serializers.CharField(),
                'amountPaid': drf_serializers.IntegerField(),
                'message': drf_serializers.CharField(),
            },
        ),
    },
)

_DevSimulateRequestSchema = inline_serializer(
    name='DevSimulateRequest',
    fields={
        'status': drf_serializers.ChoiceField(
            choices=['completed', 'failed'],
            required=False,
            help_text='Desired payment outcome. Defaults to "completed".',
        ),
    },
)


_GatewayErrorSchema = inline_serializer(
    name='GatewayErrorResponse',
    fields={
        'error': inline_serializer(
            name='GatewayErrorBody',
            fields={
                'code': drf_serializers.CharField(),
                'message': drf_serializers.CharField(),
            },
        ),
    },
)


class EnrollmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Enrollments'],
        summary='List user enrollments',
        description=(
            'Return all enrollments belonging to the authenticated user. '
            'Supports optional **paymentStatus** query parameter to filter by '
            'payment status (pending, partial, completed).'
        ),
        parameters=[
            {
                'name': 'paymentStatus',
                'in': 'query',
                'required': False,
                'schema': {'type': 'string', 'enum': ['pending', 'partial', 'completed']},
                'description': 'Filter enrollments by payment status.',
            },
        ],
        responses={
            200: _EnrollmentListResponseSchema,
            401: _ErrorResponseSchema,
        },
    )
    def get(self, request):
        qs = Enrollment.objects.filter(user=request.user).exclude(payment_status='cancelled').select_related('program').prefetch_related('payments', 'program__degrees__steps')

        payment_status = request.query_params.get('paymentStatus')
        if payment_status:
            qs = qs.filter(payment_status=payment_status)

        serializer = EnrollmentListSerializer(qs, many=True)
        return Response({'data': serializer.data})

    @extend_schema(
        tags=['Enrollments'],
        summary='Create enrollment',
        description=(
            'Enroll the authenticated user in a program. The program must be '
            'active and the user must not already be enrolled. '
            'Payment type determines the payment schedule: **full** requires a '
            'single payment of the total amount, **installment** splits the '
            'total into two equal payments (first half unlocks first-degree '
            'content, second half unlocks the rest).'
        ),
        request=EnrollmentCreateSerializer,
        responses={
            201: _EnrollmentCreateResponseSchema,
            400: _ErrorResponseSchema,
            404: _ErrorResponseSchema,
            409: _ErrorResponseSchema,
        },
        examples=[
            OpenApiExample(
                name='Enrollment creation request',
                value={
                    'programId': 'prog_abc123',
                    'paymentType': 'installment',
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Enrollment created',
                value={
                    'data': {
                        'id': 'enr_xyz789',
                        'programId': 'prog_abc123',
                        'userId': 'usr_001',
                        'paymentType': 'installment',
                        'paymentStatus': 'pending',
                        'amountPaid': 0,
                        'totalAmount': 50000,
                        'installmentAmount': 25000,
                        'enrollmentDate': '2026-02-22T10:00:00Z',
                        'payments': [],
                    }
                },
                response_only=True,
                status_codes=['201'],
            ),
        ],
    )
    def post(self, request):
        serializer = EnrollmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            details = [{'field': f, 'message': str(m[0])} for f, m in serializer.errors.items()]
            raise ValidationError('Validation failed.', details)

        program_id = serializer.validated_data['programId']
        payment_type = serializer.validated_data['paymentType']

        try:
            program = Program.objects.get(id=program_id, is_active=True)
        except Program.DoesNotExist:
            raise NotFoundError('Program does not exist.')

        # Delete cancelled enrollments and their orphaned progress to allow re-enrollment
        cancelled = Enrollment.objects.filter(
            user=request.user, program=program, payment_status='cancelled'
        )
        if cancelled.exists():
            _cleanup_enrollment_progress(request.user, program)
            cancelled.delete()

        if Enrollment.objects.filter(user=request.user, program=program).exists():
            raise ConflictError('User already enrolled in this program.')

        # Handle optional promo code
        promo_code_str = serializer.validated_data.get('promoCode', '').strip()
        promo = None
        discount = 0

        if promo_code_str:
            try:
                promo = PromoCode.objects.get(code=promo_code_str.upper())
            except PromoCode.DoesNotExist:
                raise ValidationError(
                    'Code promo invalide.',
                    [{'field': 'promoCode', 'message': 'Code promo invalide.'}],
                )

            if not promo.is_valid:
                raise ValidationError(
                    'Code promo expire ou deja utilise.',
                    [{'field': 'promoCode', 'message': 'Code promo expire ou deja utilise.'}],
                )

            already_used = PromoCodeRedemption.objects.filter(
                promo_code=promo, user=request.user
            ).exists()
            if already_used:
                raise ValidationError(
                    'Vous avez deja utilise ce code.',
                    [{'field': 'promoCode', 'message': 'Vous avez deja utilise ce code.'}],
                )

            discount = math.floor(program.price * promo.discount_percent / 100)

        total_amount = program.price - discount

        enrollment = Enrollment.objects.create(
            user=request.user,
            program=program,
            payment_type=payment_type,
            total_amount=total_amount,
            installment_config_snapshot={
                'num_installments': program.num_installments,
                'degrees_per_installment': program.degrees_per_installment,
                'completion_threshold': program.completion_threshold,
            },
        )

        # Record promo code redemption if used
        if promo:
            PromoCodeRedemption.objects.create(
                promo_code=promo,
                user=request.user,
                enrollment=enrollment,
                discount_applied=discount,
            )
            promo.current_uses += 1
            promo.save()

        data = {
            'id': enrollment.id,
            'programId': enrollment.program_id,
            'userId': enrollment.user_id,
            'paymentType': enrollment.payment_type,
            'paymentStatus': enrollment.payment_status,
            'amountPaid': enrollment.amount_paid,
            'totalAmount': enrollment.total_amount,
            'installmentAmount': enrollment.installment_amount,
            'enrollmentDate': enrollment.enrollment_date,
            'payments': [],
        }

        if promo:
            data['promoCodeApplied'] = promo.code
            data['discountApplied'] = discount

        return Response({'data': data}, status=status.HTTP_201_CREATED)


class EnrollmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Enrollments'],
        summary='Get enrollment detail',
        description=(
            'Return a single enrollment with full detail including remaining '
            'amount, installment amount, degree-level access information, and '
            'payment history. The authenticated user must own the enrollment.'
        ),
        responses={
            200: EnrollmentDetailSerializer,
            403: _ErrorResponseSchema,
            404: _ErrorResponseSchema,
        },
    )
    def get(self, request, enrollment_id):
        try:
            enrollment = Enrollment.objects.select_related('program').prefetch_related(
                'payments', 'program__degrees'
            ).get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            raise NotFoundError('Enrollment does not exist.')

        if enrollment.user_id != request.user.id:
            raise ForbiddenError('Enrollment belongs to another user.')

        serializer = EnrollmentDetailSerializer(enrollment)
        return Response(serializer.data)


class EnrollmentPendingPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id):
        from apps.enrollments.utils import check_and_expire_payment
        from datetime import timedelta

        payment = Payment.objects.filter(
            enrollment_id=enrollment_id,
            enrollment__user=request.user,
            status='pending'
        ).order_by('-created_at').first()

        if not payment:
            return Response({'detail': 'No pending payment'}, status=404)

        payment = check_and_expire_payment(payment)
        if payment.status != 'pending':
            return Response({'detail': 'No pending payment'}, status=404)

        expiry_minutes = getattr(settings, 'PAYMENT_EXPIRY_MINUTES', 15)
        return Response({
            'paymentId': payment.id,
            'paymentUrl': payment.payment_url or None,
            'amount': payment.amount,
            'method': payment.method,
            'status': payment.status,
            'createdAt': payment.created_at,
            'expiresAt': payment.created_at + timedelta(minutes=expiry_minutes),
        })


class PaymentInitiateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentThrottle]

    @extend_schema(
        tags=['Payments'],
        summary='Initiate payment',
        description=(
            'Initiate a mobile-money payment through the MoneyFusion gateway. '
            'The **amount** must match the expected value: for **full** payment '
            'type it must equal the total program price; for **installment** the '
            'first payment is ceil(totalAmount / 2) and the second covers the '
            'remainder. Only one pending payment per enrollment is allowed at a '
            'time. A successful response returns a payment ID, a MoneyFusion '
            'transaction ID, and an optional payment URL. The payment expires '
            'after 30 minutes if not confirmed on the user\'s phone.'
        ),
        request=PaymentInitiateSerializer,
        responses={
            200: _PaymentInitiateResponseSchema,
            400: _ErrorResponseSchema,
            403: _ErrorResponseSchema,
            404: _ErrorResponseSchema,
            409: _ErrorResponseSchema,
            429: _ErrorResponseSchema,
            502: _GatewayErrorSchema,
        },
        examples=[
            OpenApiExample(
                name='Payment initiation request',
                value={
                    'enrollmentId': 'enr_xyz789',
                    'amount': 25000,
                    'method': 'orangeMoney',
                    'phone': '+2250700000000',
                },
                request_only=True,
            ),
            OpenApiExample(
                name='Payment initiated',
                value={
                    'data': {
                        'paymentId': 'pay_abc456',
                        'transactionId': 'mf_txn_12345',
                        'status': 'pending',
                        'message': 'Paiement initie avec succes. Veuillez confirmer sur votre telephone.',
                        'expiresAt': '2026-02-22T10:30:00Z',
                        'paymentUrl': 'https://pay.moneyfusion.com/txn/12345',
                    }
                },
                response_only=True,
                status_codes=['200'],
            ),
        ],
    )
    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            details = [{'field': f, 'message': str(m[0])} for f, m in serializer.errors.items()]
            raise ValidationError('Validation failed.', details)

        enrollment_id = serializer.validated_data['enrollmentId']
        amount = serializer.validated_data['amount']
        method = serializer.validated_data.get('method', 'orangeMoney')
        phone = serializer.validated_data.get('phone', '') or request.user.phone or ''

        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            raise NotFoundError('Enrollment does not exist.')

        if enrollment.user_id != request.user.id:
            raise ForbiddenError('Enrollment belongs to another user.')

        if enrollment.payment_status == 'completed':
            raise ConflictError('Payment already completed.')

        # Amount validation
        remaining = enrollment.total_amount - enrollment.amount_paid
        if enrollment.payment_type == 'full':
            expected = enrollment.total_amount
        elif enrollment.amount_paid == 0:
            snapshot = enrollment.installment_config_snapshot or {}
            num_inst = snapshot.get('num_installments') or enrollment.program.num_installments or 2
            expected = math.ceil(enrollment.total_amount / num_inst)
        else:
            expected = remaining

        if amount != expected:
            raise ValidationError(
                f'Expected payment amount: {expected} XOF.',
                [{'field': 'amount', 'message': f'Expected {expected}, got {amount}'}]
            )

        # Auto-expire stale pending payments
        from apps.enrollments.utils import check_and_expire_payment
        pending_payments = Payment.objects.filter(
            enrollment=enrollment,
            status='pending',
        )
        for p in pending_payments:
            check_and_expire_payment(p)

        # Check for non-stale pending payments
        if Payment.objects.filter(enrollment=enrollment, status='pending').exists():
            raise ConflictError('A payment is already pending for this enrollment.')

        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=amount,
            method=method,
        )

        # Initiate with MoneyFusion
        try:
            mf_result = MoneyFusionService.initiate_payment(payment, phone)
        except MoneyFusionError as e:
            payment.status = 'failed'
            payment.save()
            return Response({
                'error': {
                    'code': 'PAYMENT_GATEWAY_ERROR',
                    'message': str(e),
                }
            }, status=status.HTTP_502_BAD_GATEWAY)

        payment.mf_transaction_id = mf_result.get('transactionId', '')
        payment.payment_url = mf_result.get('paymentUrl', '') or ''
        payment.save(update_fields=['mf_transaction_id', 'payment_url', 'updated_at'])

        expires_at = timezone.now() + timedelta(minutes=settings.PAYMENT_EXPIRY_MINUTES)

        response_data = {
            'paymentId': payment.id,
            'transactionId': mf_result['transactionId'],
            'status': 'pending',
            'message': 'Paiement initie avec succes. Veuillez confirmer sur votre telephone.',
            'expiresAt': expires_at.isoformat(),
        }

        if mf_result.get('paymentUrl'):
            response_data['paymentUrl'] = mf_result['paymentUrl']

        return Response({'data': response_data})


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payments'],
        summary='Check payment status',
        description=(
            'Retrieve the current status of a payment. Returns the payment '
            'status (pending, completed, failed), amount, method, transaction '
            'reference, and the MoneyFusion transaction ID. The authenticated '
            'user must own the enrollment associated with the payment.'
        ),
        responses={
            200: PaymentStatusSerializer,
            403: _ErrorResponseSchema,
            404: _ErrorResponseSchema,
        },
    )
    def get(self, request, payment_id):
        from apps.enrollments.utils import check_and_expire_payment

        try:
            payment = Payment.objects.select_related('enrollment').get(id=payment_id)
        except Payment.DoesNotExist:
            raise NotFoundError('Payment does not exist.')

        if payment.enrollment.user_id != request.user.id:
            raise ForbiddenError('Payment belongs to another user.')

        payment = check_and_expire_payment(payment)

        serializer = PaymentStatusSerializer(payment)
        return Response(serializer.data)


class PaymentHistoryView(APIView):
    """List all payments for the authenticated user across all enrollments."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payments'],
        summary='Get payment history',
        description='Returns all payments for the authenticated user across all enrollments, ordered by date descending.',
        parameters=[
            {
                'name': 'status',
                'in': 'query',
                'required': False,
                'schema': {'type': 'string'},
                'description': 'Filter by payment status (completed, pending, failed, expired).',
            },
            {
                'name': 'method',
                'in': 'query',
                'required': False,
                'schema': {'type': 'string'},
                'description': 'Filter by payment method (orangeMoney, mtnMoney, wave).',
            },
        ],
        responses={
            200: PaymentHistorySerializer(many=True),
        },
    )
    def get(self, request):
        payments = Payment.objects.filter(
            enrollment__user=request.user
        ).select_related(
            'enrollment', 'enrollment__program'
        ).order_by('-created_at')

        # Optional filters
        status = request.query_params.get('status')
        if status:
            payments = payments.filter(status=status)
        method = request.query_params.get('method')
        if method:
            payments = payments.filter(method=method)

        serializer = PaymentHistorySerializer(payments, many=True)
        return Response({'data': serializer.data})


class PaymentVerifyView(APIView):
    """Verify payment status by MoneyFusion token.

    Called by the frontend confirmation page after MoneyFusion redirects
    the user back with ?token=<mf_token>.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Payments'],
        summary='Verify payment by token',
        description=(
            'Look up a payment by its MoneyFusion token and return its current '
            'status. This is called by the payment confirmation page after '
            'MoneyFusion redirects the user back. No authentication required '
            'since the token acts as a capability.'
        ),
        parameters=[
            {
                'name': 'token',
                'in': 'query',
                'required': True,
                'schema': {'type': 'string'},
                'description': 'MoneyFusion payment token.',
            },
        ],
        responses={
            200: inline_serializer(
                name='PaymentVerifyResponse',
                fields={
                    'data': inline_serializer(
                        name='PaymentVerifyData',
                        fields={
                            'status': drf_serializers.CharField(),
                            'paymentId': drf_serializers.CharField(),
                            'amount': drf_serializers.IntegerField(),
                            'enrollmentId': drf_serializers.CharField(),
                        },
                    ),
                },
            ),
            404: _ErrorResponseSchema,
        },
    )
    def get(self, request):
        from apps.enrollments.utils import check_and_expire_payment

        token = request.query_params.get('token')
        if not token:
            raise ValidationError(
                'Token is required.',
                [{'field': 'token', 'message': 'Token query parameter is required.'}],
            )

        # Find payment by MoneyFusion transaction ID (token)
        payment = Payment.objects.filter(mf_transaction_id=token).select_related('enrollment', 'enrollment__program').first()
        if not payment:
            raise NotFoundError('Payment not found for this token.')

        payment = check_and_expire_payment(payment)

        # If still pending, verify with MoneyFusion API
        if payment.status == 'pending':
            try:
                mf_result = MoneyFusionService.verify_payment(token)
                mf_status = mf_result.get('data', {}).get('statut', '')
                if mf_status == 'paid':
                    _complete_payment(payment.id)
                    payment.refresh_from_db()
                elif mf_status in ('failed', 'failure', 'no paid'):
                    payment.status = 'failed'
                    payment.save()
            except Exception:
                pass  # Fall through and return current DB status

        enrollment = payment.enrollment
        program = enrollment.program if enrollment else None
        return Response({
            'data': {
                'status': payment.status,
                'paymentId': payment.id,
                'amount': payment.amount,
                'enrollmentId': payment.enrollment_id,
                'programId': program.id if program else '',
                'programName': program.name if program else '',
                'enrollmentPaymentStatus': enrollment.payment_status if enrollment else '',
            }
        })


class PaymentWebhookView(APIView):
    """Receives payment status updates from MoneyFusion.

    MoneyFusion POSTs a payload with nested data including tokenPay and statut.
    We verify authenticity by calling get_payment(token) via the API.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Payments'],
        summary='MoneyFusion webhook callback',
        description=(
            'Receives asynchronous payment status updates from MoneyFusion. '
            'The payload contains a nested data object with tokenPay and statut fields. '
            'Authenticity is verified by calling get_payment() on the MoneyFusion API. '
            'On a "paid" status, the payment is completed atomically and the '
            'enrollment is updated. The handler is idempotent.'
        ),
        request=inline_serializer(
            name='MFWebhookRequest',
            fields={
                'statut': drf_serializers.BooleanField(),
                'data': inline_serializer(
                    name='MFWebhookData',
                    fields={
                        'tokenPay': drf_serializers.CharField(),
                        'statut': drf_serializers.CharField(),
                        'Montant': drf_serializers.CharField(required=False),
                        'moyen': drf_serializers.CharField(required=False),
                    },
                ),
            },
        ),
        responses={
            200: _WebhookReceivedSchema,
            404: _ErrorResponseSchema,
        },
    )
    def post(self, request):
        data = request.data
        logger.info('Webhook raw payload: %s', data)

        # MoneyFusion may send tokenPay at different nesting levels
        mf_data = data.get('data', {})
        token = mf_data.get('tokenPay', '') or data.get('tokenPay', '')
        mf_status = mf_data.get('statut', '') or data.get('statut', '')

        if not token:
            logger.warning('Webhook received with no tokenPay. Keys: %s', list(data.keys()))
            return Response({'received': True})

        # Find payment by MoneyFusion token
        payment = Payment.objects.filter(mf_transaction_id=token).first()
        if not payment:
            logger.warning('Webhook received for unknown token: %s', token)
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Payment not found.'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Idempotency: already processed
        if payment.status in ('completed', 'failed'):
            return Response({'received': True})

        # Verify with MoneyFusion API
        try:
            verify_result = MoneyFusionService.verify_payment(token)
            verified_status = verify_result.get('data', {}).get('statut', '')
        except Exception:
            logger.exception('Failed to verify webhook for token %s', token)
            verified_status = mf_status  # Fall back to webhook data

        if verified_status == 'paid':
            _complete_payment(payment.id)
        elif verified_status in ('failed', 'failure', 'no paid'):
            payment.status = 'failed'
            payment.save()

        return Response({'received': True})


class EnrollmentPaymentsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payments'],
        summary='List enrollment payments',
        description=(
            'Return all payments associated with a specific enrollment, '
            'ordered by date descending (most recent first). The authenticated '
            'user must own the enrollment.'
        ),
        responses={
            200: _PaymentListResponseSchema,
            403: _ErrorResponseSchema,
            404: _ErrorResponseSchema,
        },
    )
    def get(self, request, enrollment_id):
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            raise NotFoundError('Enrollment does not exist.')

        if enrollment.user_id != request.user.id:
            raise ForbiddenError('Enrollment belongs to another user.')

        payments = enrollment.payments.all().order_by('-date')
        serializer = PaymentSerializer(payments, many=True)
        return Response({'data': serializer.data})


class DevPaymentSimulateView(APIView):
    """DEV ONLY: Simulate MoneyFusion webhook callback for a pending payment.

    This triggers the same webhook processing as a real MoneyFusion callback,
    allowing E2E testing without a real payment gateway. The endpoint builds
    a valid signed webhook payload and processes it through the webhook handler.

    Only available when MONEYFUSION_DEV_MODE=True.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payments'],
        summary='Simulate payment (dev only)',
        description=(
            '**Development only.** Simulate a MoneyFusion webhook callback for '
            'a pending payment. Builds a properly signed webhook payload and '
            'processes it through the same webhook handler used in production. '
            'The optional **status** field in the request body controls the '
            'simulated outcome ("completed" or "failed"); defaults to '
            '"completed". Returns the updated payment and enrollment state. '
            'Returns 403 when MONEYFUSION_DEV_MODE is not enabled.'
        ),
        request=_DevSimulateRequestSchema,
        responses={
            200: _DevSimulateResponseSchema,
            403: _ErrorResponseSchema,
            404: _ErrorResponseSchema,
            409: _ErrorResponseSchema,
        },
        examples=[
            OpenApiExample(
                name='Simulate completed payment',
                value={'status': 'completed'},
                request_only=True,
            ),
            OpenApiExample(
                name='Simulation result',
                value={
                    'data': {
                        'paymentId': 'pay_abc456',
                        'status': 'completed',
                        'enrollmentPaymentStatus': 'partial',
                        'amountPaid': 25000,
                        'message': 'Payment simulated as completed.',
                    }
                },
                response_only=True,
                status_codes=['200'],
            ),
        ],
    )
    @transaction.atomic
    def post(self, request, payment_id):
        from django.conf import settings as django_settings

        if not django_settings.MONEYFUSION_DEV_MODE:
            return Response(
                {'error': {'code': 'FORBIDDEN', 'message': 'Only available in dev mode.'}},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            payment = Payment.objects.select_related('enrollment').get(id=payment_id)
        except Payment.DoesNotExist:
            raise NotFoundError('Payment does not exist.')

        if payment.enrollment.user_id != request.user.id:
            raise ForbiddenError('Payment belongs to another user.')

        if payment.status != 'pending':
            raise ConflictError(f'Payment is already {payment.status}.')

        # Map user-facing status to MoneyFusion status
        simulate_status = request.data.get('status', 'completed')
        if simulate_status not in ('completed', 'failed'):
            raise ValidationError(
                'status must be "completed" or "failed".',
                [{'field': 'status', 'message': 'Must be "completed" or "failed"'}],
            )

        mf_status = 'paid' if simulate_status == 'completed' else 'failure'

        # Build MoneyFusion-format webhook payload and process
        payload = MoneyFusionService.build_dev_webhook_payload(payment, mf_status)

        # Process through the webhook handler
        webhook_view = PaymentWebhookView()
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        webhook_request = factory.post(
            '/api/v1/payments/webhook',
            data=payload,
            format='json',
        )
        webhook_view.post(webhook_request)

        # Reload to get updated status
        payment.refresh_from_db()
        enrollment = payment.enrollment
        enrollment.refresh_from_db()

        return Response({
            'data': {
                'paymentId': payment.id,
                'status': payment.status,
                'enrollmentPaymentStatus': enrollment.payment_status,
                'amountPaid': enrollment.amount_paid,
                'message': f'Payment simulated as {simulate_status}.',
            }
        })


class PromoCodeGenerateView(APIView):
    """Generate a promo code. Admin only."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Only admins can generate promo codes
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only administrators can generate promo codes.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Create promo code (default 20% discount, 1 use, expires in 30 days)
        promo = PromoCode.objects.create(
            creator=request.user,
            discount_percent=20,
            max_uses=1,
            expires_at=timezone.now() + timedelta(days=30),
        )
        return Response(PromoCodeSerializer(promo).data, status=status.HTTP_201_CREATED)


class PromoCodeValidateView(APIView):
    """Validate a promo code and return discount info."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PromoCodeValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code'].upper()
        try:
            promo = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            return Response({'valid': False, 'error': 'Code promo invalide.'}, status=status.HTTP_404_NOT_FOUND)

        if not promo.is_valid:
            return Response(
                {'valid': False, 'error': 'Code promo expire ou deja utilise.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user already used this code
        already_used = PromoCodeRedemption.objects.filter(promo_code=promo, user=request.user).exists()
        if already_used:
            return Response(
                {'valid': False, 'error': 'Vous avez deja utilise ce code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'valid': True,
            'code': promo.code,
            'discountPercent': promo.discount_percent,
        })


class PromoCodeListView(APIView):
    """List promo codes created by the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        codes = PromoCode.objects.filter(creator=request.user).order_by('-created_at')
        return Response(PromoCodeSerializer(codes, many=True).data)


_MONTHS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


class AttestationView(APIView):
    """Generate and stream a personalised PDF attestation for a completed enrollment."""
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id):
        import io as _io
        import logging
        from django.http import FileResponse
        from docxtpl import DocxTemplate
        from apps.progress.models import QCMAttempt
        from django.db.models import Max
        from minio import Minio

        logger = logging.getLogger(__name__)

        # 1. Fetch + authorisation
        try:
            enrollment = Enrollment.objects.select_related('user', 'program').get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return Response({'error': 'Inscription introuvable'}, status=404)

        if enrollment.user != request.user and not request.user.is_staff:
            return Response({'error': 'Accès interdit'}, status=403)

        if not enrollment.all_degrees_completed():
            return Response({'error': 'Programme non terminé'}, status=403)

        program = enrollment.program
        user = enrollment.user

        # 2. participant_name
        participant_name = f"{user.first_name} {user.last_name}".strip() or user.phone

        # 3. duration
        w = program.duration_weeks
        duration = f"{w // 4} mois" if w % 4 == 0 else f"{w} semaines"

        # 4. date + year
        today = date.today()
        date_str = f"{today.day:02d} {_MONTHS_FR[today.month - 1]} {today.year}"
        year = str(today.year)

        # 5. mention — best score per QCM asset averaged across the program
        scores_qs = (
            QCMAttempt.objects
            .filter(user=user, asset__step__degree__program=program)
            .values('asset_id')
            .annotate(best=Max('score'))
        )
        scores = list(scores_qs)
        if scores:
            avg = sum(float(s['best']) for s in scores) / len(scores)
            if avg >= 90:
                mention = "EXCELLENT"
            elif avg >= 80:
                mention = "TRÈS BIEN"
            else:
                mention = "BIEN"
        else:
            mention = "BIEN"

        # 6. modules — admin-defined text or fallback from degrees/steps
        if program.modules_text:
            modules = program.modules_text
        else:
            parts = []
            for degree in program.degrees.order_by('order_index').prefetch_related('steps'):
                step_titles = " - ".join(
                    s.title for s in degree.steps.order_by('order_index')
                )
                parts.append(
                    f"{degree.title} : {step_titles}" if step_titles else degree.title
                )
            modules = " | ".join(parts)

        # 7. Render DOCX template
        template_path = os.path.join(
            settings.BASE_DIR, 'apps', 'content', 'attestation_template_FINAL.docx'
        )
        tpl = DocxTemplate(template_path)
        tpl.render({
            'participant_name': participant_name,
            'program_name': program.name,
            'duration': duration,
            'year': year,
            'date': date_str,
            'mention': mention,
            'modules': modules,
        })

        # 8. Write DOCX to /tmp, convert to PDF via LibreOffice
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False, dir='/tmp') as f:
            docx_path = f.name
        tpl.save(docx_path)

        subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', '/tmp', docx_path],
            check=True,
            capture_output=True,
            timeout=60,
        )
        pdf_path = docx_path.replace('.docx', '.pdf')

        # 9. Upload to MinIO (documents bucket) — best-effort, non-fatal
        try:
            pdf_bytes = open(pdf_path, 'rb').read()
            minio_endpoint = (
                f"{settings.MINIO_ENDPOINT}:{settings.MINIO_PORT}"
                if settings.MINIO_PORT not in (80, 443)
                else settings.MINIO_ENDPOINT
            )
            minio_client = Minio(
                minio_endpoint,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_SSL,
            )
            minio_key = f"attestations/{enrollment_id}.pdf"
            minio_client.put_object(
                settings.MINIO_DOCUMENT_BUCKET,
                minio_key,
                _io.BytesIO(pdf_bytes),
                length=len(pdf_bytes),
                content_type='application/pdf',
            )
            logger.info("Attestation uploaded to MinIO: %s/%s", settings.MINIO_DOCUMENT_BUCKET, minio_key)
        except Exception as exc:
            logger.warning("MinIO upload failed for attestation %s: %s", enrollment_id, exc)

        # 10. Stream PDF then clean up temp files in background
        def _cleanup():
            import time
            time.sleep(10)
            for p in (docx_path, pdf_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass

        threading.Thread(target=_cleanup, daemon=True).start()

        safe_name = enrollment_id.replace('/', '_')
        return FileResponse(
            open(pdf_path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"attestation_{safe_name}.pdf",
        )
