import math
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample

from apps.core.exceptions import ConflictError, NotFoundError, ValidationError
from apps.programs.models import Program

from .models import Enrollment, PromoCode, PromoCodeRedemption
from .serializers import EnrollmentCreateSerializer, EnrollmentListSerializer
from .views_helpers import _cleanup_enrollment_progress
from .views_schemas import (
    _EnrollmentListResponseSchema,
    _EnrollmentCreateResponseSchema,
    _ErrorResponseSchema,
)

logger = logging.getLogger(__name__)


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
        responses={200: _EnrollmentListResponseSchema, 401: _ErrorResponseSchema},
    )
    def get(self, request):
        qs = (
            Enrollment.objects
            .filter(user=request.user)
            .exclude(payment_status='cancelled')
            .select_related('program')
            .prefetch_related('payments', 'program__degrees__steps')
        )
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
            'Payment type: **full** = single payment, **installment** = two payments.'
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
                value={'programId': 'prog_abc123', 'paymentType': 'installment'},
                request_only=True,
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

        cancelled = Enrollment.objects.filter(
            user=request.user, program=program, payment_status='cancelled'
        )
        if cancelled.exists():
            _cleanup_enrollment_progress(request.user, program)
            cancelled.delete()

        if Enrollment.objects.filter(user=request.user, program=program).exists():
            raise ConflictError('User already enrolled in this program.')

        # Handle optional mandataire
        mandataire_id = (serializer.validated_data.get('mandataireId') or '').strip() or None
        if mandataire_id:
            from apps.accounts.models import User as UserModel
            if not UserModel.objects.filter(id=mandataire_id, is_mandataire=True).exists():
                raise ValidationError(
                    'Mandataire invalide.',
                    [{'field': 'mandataireId', 'message': 'Utilisateur non désigné comme mandataire.'}],
                )

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
            mandataire_id=mandataire_id,
            installment_config_snapshot={
                'num_installments': program.num_installments,
                'degrees_per_installment': program.degrees_per_installment,
                'completion_threshold': program.completion_threshold,
            },
        )

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
