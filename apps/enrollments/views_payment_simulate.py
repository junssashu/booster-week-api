from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample

from apps.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError

from .models import Payment
from .services import MoneyFusionService
from .views_schemas import _DevSimulateResponseSchema, _DevSimulateRequestSchema, _ErrorResponseSchema


class DevPaymentSimulateView(APIView):
    """DEV ONLY: Simulate MoneyFusion webhook callback for a pending payment."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payments'],
        summary='Simulate payment (dev only)',
        description=(
            '**Development only.** Simulate a MoneyFusion webhook callback for '
            'a pending payment. Returns 403 when MONEYFUSION_DEV_MODE is not enabled.'
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
        ],
    )
    @transaction.atomic
    def post(self, request, payment_id):
        from django.conf import settings as django_settings
        from .views_payment_webhook import PaymentWebhookView

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

        simulate_status = request.data.get('status', 'completed')
        if simulate_status not in ('completed', 'failed'):
            raise ValidationError(
                'status must be "completed" or "failed".',
                [{'field': 'status', 'message': 'Must be "completed" or "failed"'}],
            )

        mf_status = 'paid' if simulate_status == 'completed' else 'failure'
        payload = MoneyFusionService.build_dev_webhook_payload(payment, mf_status)

        webhook_view = PaymentWebhookView()
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        webhook_request = factory.post('/api/v1/payments/webhook', data=payload, format='json')
        webhook_view.post(webhook_request)

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
