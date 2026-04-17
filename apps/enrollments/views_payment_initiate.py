import math
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample

from apps.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from apps.core.throttles import PaymentThrottle

from .models import Enrollment, Payment
from .serializers import PaymentInitiateSerializer
from .services import MoneyFusionError, MoneyFusionService
from .views_schemas import (
    _PaymentInitiateResponseSchema,
    _ErrorResponseSchema,
    _GatewayErrorSchema,
)

logger = logging.getLogger(__name__)


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
            'time.'
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

        from apps.enrollments.utils import check_and_expire_payment
        for p in Payment.objects.filter(enrollment=enrollment, status='pending'):
            check_and_expire_payment(p)

        if Payment.objects.filter(enrollment=enrollment, status='pending').exists():
            raise ConflictError('A payment is already pending for this enrollment.')

        payment = Payment.objects.create(enrollment=enrollment, amount=amount, method=method)

        try:
            mf_result = MoneyFusionService.initiate_payment(payment, phone)
        except MoneyFusionError as e:
            payment.status = 'failed'
            payment.save()
            return Response(
                {'error': {'code': 'PAYMENT_GATEWAY_ERROR', 'message': str(e)}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

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
