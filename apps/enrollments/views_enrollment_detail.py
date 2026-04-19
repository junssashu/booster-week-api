from datetime import timedelta

from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.core.exceptions import ForbiddenError, NotFoundError

from .models import Enrollment, Payment
from .serializers import EnrollmentDetailSerializer
from .views_schemas import _ErrorResponseSchema


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
