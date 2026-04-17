from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.core.exceptions import ForbiddenError, NotFoundError

from .models import Payment
from .serializers import PaymentHistorySerializer, PaymentSerializer, PaymentStatusSerializer
from .views_schemas import _ErrorResponseSchema, _PaymentListResponseSchema


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payments'],
        summary='Check payment status',
        description=(
            'Retrieve the current status of a payment. The authenticated '
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
            {'name': 'status', 'in': 'query', 'required': False,
             'schema': {'type': 'string'}, 'description': 'Filter by payment status.'},
            {'name': 'method', 'in': 'query', 'required': False,
             'schema': {'type': 'string'}, 'description': 'Filter by payment method.'},
        ],
        responses={200: PaymentHistorySerializer(many=True)},
    )
    def get(self, request):
        payments = (
            Payment.objects
            .filter(enrollment__user=request.user)
            .select_related('enrollment', 'enrollment__program')
            .order_by('-created_at')
        )
        status_filter = request.query_params.get('status')
        if status_filter:
            payments = payments.filter(status=status_filter)
        method = request.query_params.get('method')
        if method:
            payments = payments.filter(method=method)
        serializer = PaymentHistorySerializer(payments, many=True)
        return Response({'data': serializer.data})


class EnrollmentPaymentsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Payments'],
        summary='List enrollment payments',
        description=(
            'Return all payments associated with a specific enrollment, '
            'ordered by date descending. The authenticated user must own the enrollment.'
        ),
        responses={
            200: _PaymentListResponseSchema,
            403: _ErrorResponseSchema,
            404: _ErrorResponseSchema,
        },
    )
    def get(self, request, enrollment_id):
        from .models import Enrollment
        from apps.core.exceptions import ForbiddenError, NotFoundError

        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            raise NotFoundError('Enrollment does not exist.')

        if enrollment.user_id != request.user.id:
            raise ForbiddenError('Enrollment belongs to another user.')

        payments = enrollment.payments.all().order_by('-date')
        serializer = PaymentSerializer(payments, many=True)
        return Response({'data': serializer.data})
