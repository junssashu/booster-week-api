from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrAssistant, IsAdminOrAssistantNoCreateDelete
from apps.enrollments.models import Enrollment, Payment
from .serializers import (
    AdminEnrollmentSerializer, AdminEnrollmentWriteSerializer, AdminPaymentSerializer,
)


class AdminEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related('user', 'program', 'mandataire').order_by('-created_at')
    permission_classes = [IsAdminOrAssistantNoCreateDelete]

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return AdminEnrollmentWriteSerializer
        return AdminEnrollmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        program_id = self.request.query_params.get('programId')
        user_id = self.request.query_params.get('userId')
        if status:
            qs = qs.filter(payment_status=status)
        if program_id:
            qs = qs.filter(program_id=program_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        mandataire_id = self.request.query_params.get('mandataireId')
        if mandataire_id == 'none':
            qs = qs.filter(mandataire__isnull=True)
        elif mandataire_id:
            qs = qs.filter(mandataire_id=mandataire_id)
        return qs

    def perform_destroy(self, instance):
        from apps.enrollments.views import _cleanup_enrollment_progress
        _cleanup_enrollment_progress(instance.user, instance.program)
        if instance.payments.exists():
            instance.payment_status = 'cancelled'
            instance.save(update_fields=['payment_status'])
        else:
            instance.delete()

    @action(detail=True, methods=['get'], url_path='invoice')
    def invoice(self, request, pk=None):
        enrollment = self.get_object()
        payments = enrollment.payments.filter(status='completed').order_by('date')
        return Response({'data': {
            'invoiceNumber': f'BWC-{enrollment.id.upper()}-{enrollment.created_at.strftime("%Y%m%d")}',
            'student': {
                'name': f'{enrollment.user.first_name} {enrollment.user.last_name}',
                'phone': enrollment.user.phone,
                'email': enrollment.user.email,
            },
            'program': {
                'name': enrollment.program.name,
                'price': enrollment.program.price,
            },
            'enrollment': {
                'id': enrollment.id,
                'paymentType': enrollment.payment_type,
                'paymentStatus': enrollment.payment_status,
                'amountPaid': enrollment.amount_paid,
                'totalAmount': enrollment.total_amount,
                'enrollmentDate': enrollment.enrollment_date,
            },
            'payments': [{
                'amount': p.amount,
                'method': p.method,
                'date': p.date,
                'transactionRef': p.transaction_ref,
            } for p in payments],
        }})


class AdminPaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminPaymentSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = Payment.objects.select_related(
            'enrollment', 'enrollment__user', 'enrollment__program',
        ).order_by('-created_at')
        payment_status = self.request.query_params.get('status')
        if payment_status:
            qs = qs.filter(status=payment_status)
        method = self.request.query_params.get('method')
        if method:
            qs = qs.filter(method=method)
        return qs
