import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers

from apps.core.exceptions import NotFoundError, ValidationError

from .models import Payment
from .services import MoneyFusionService
from .views_helpers import _complete_payment
from .views_schemas import _ErrorResponseSchema, _WebhookReceivedSchema

logger = logging.getLogger(__name__)


class PaymentVerifyView(APIView):
    """Verify payment status by MoneyFusion token."""
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Payments'],
        summary='Verify payment by token',
        description=(
            'Look up a payment by its MoneyFusion token and return its current status. '
            'No authentication required since the token acts as a capability.'
        ),
        parameters=[
            {'name': 'token', 'in': 'query', 'required': True,
             'schema': {'type': 'string'}, 'description': 'MoneyFusion payment token.'},
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

        payment = Payment.objects.filter(mf_transaction_id=token).select_related(
            'enrollment', 'enrollment__program'
        ).first()
        if not payment:
            raise NotFoundError('Payment not found for this token.')

        payment = check_and_expire_payment(payment)

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
                pass

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
    """Receives payment status updates from MoneyFusion."""
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Payments'],
        summary='MoneyFusion webhook callback',
        description=(
            'Receives asynchronous payment status updates from MoneyFusion. '
            'Authenticity is verified by calling get_payment() on the MoneyFusion API. '
            'On a "paid" status, the payment is completed atomically. Idempotent.'
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
        responses={200: _WebhookReceivedSchema, 404: _ErrorResponseSchema},
    )
    def post(self, request):
        data = request.data
        logger.info('Webhook raw payload: %s', data)

        mf_data = data.get('data', {})
        token = mf_data.get('tokenPay', '') or data.get('tokenPay', '')
        mf_status = mf_data.get('statut', '') or data.get('statut', '')

        if not token:
            logger.warning('Webhook received with no tokenPay. Keys: %s', list(data.keys()))
            return Response({'received': True})

        payment = Payment.objects.filter(mf_transaction_id=token).first()
        if not payment:
            logger.warning('Webhook received for unknown token: %s', token)
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Payment not found.'}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment.status in ('completed', 'failed'):
            return Response({'received': True})

        try:
            verify_result = MoneyFusionService.verify_payment(token)
            verified_status = verify_result.get('data', {}).get('statut', '')
        except Exception:
            logger.exception('Failed to verify webhook for token %s', token)
            verified_status = mf_status

        if verified_status == 'paid':
            _complete_payment(payment.id)
        elif verified_status in ('failed', 'failure', 'no paid'):
            payment.status = 'failed'
            payment.save()

        return Response({'received': True})
