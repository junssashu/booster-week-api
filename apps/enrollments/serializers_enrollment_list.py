from rest_framework import serializers

from .models import Enrollment


class EnrollmentListSerializer(serializers.ModelSerializer):
    programId = serializers.CharField(source='program_id')
    programName = serializers.SerializerMethodField()
    programImageUrl = serializers.SerializerMethodField()
    userId = serializers.CharField(source='user_id')
    paymentType = serializers.CharField(source='payment_type')
    paymentStatus = serializers.CharField(source='payment_status')
    amountPaid = serializers.IntegerField(source='amount_paid')
    totalAmount = serializers.IntegerField(source='total_amount')
    enrollmentDate = serializers.DateTimeField(source='enrollment_date')
    degreeAccess = serializers.SerializerMethodField()
    program = serializers.SerializerMethodField()
    nextAction = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ['id', 'programId', 'programName', 'programImageUrl', 'userId',
                  'paymentType', 'paymentStatus', 'amountPaid', 'totalAmount',
                  'enrollmentDate', 'degreeAccess', 'program', 'nextAction']

    def get_programName(self, obj):
        return obj.program.name if obj.program else None

    def get_programImageUrl(self, obj):
        return obj.program.image_url if obj.program else None

    def get_degreeAccess(self, obj):
        from apps.progress.models import StepProgress
        degrees = obj.program.degrees.all().order_by('order_index')
        result = []
        for d in degrees:
            accessible, lock_reason = obj.can_access_degree_detail(d)
            steps = d.steps.all()
            total_steps = steps.count()
            if total_steps > 0:
                progress_records = dict(
                    StepProgress.objects.filter(
                        user=obj.user, step__in=steps
                    ).values_list('step_id', 'completion_percentage')
                )
                total_pct = sum(progress_records.get(step.id, 0) for step in steps)
                completion_pct = round(total_pct / total_steps)
            else:
                completion_pct = 0
            result.append({
                'degreeId': d.id,
                'degreeName': d.title,
                'orderIndex': d.order_index,
                'accessible': accessible,
                'lockReason': lock_reason,
                'completionPercentage': completion_pct,
            })
        return result

    def get_program(self, obj):
        return {
            'id': obj.program.id,
            'name': obj.program.name,
            'imageUrl': obj.program.image_url,
        }

    def get_nextAction(self, enrollment):
        if enrollment.payment_status in ('pending', 'partial'):
            from apps.enrollments.utils import check_and_expire_payment
            pending = enrollment.payments.filter(
                status='pending'
            ).order_by('-created_at').first()
            if pending:
                pending = check_and_expire_payment(pending)
            if pending and pending.status == 'pending':
                return {
                    'action': 'pay',
                    'enrollmentId': enrollment.id,
                    'paymentUrl': pending.payment_url or None,
                    'paymentId': str(pending.id),
                }
            else:
                return {
                    'action': 'pay',
                    'enrollmentId': enrollment.id,
                    'paymentUrl': None,
                    'paymentId': None,
                }
        elif enrollment.all_degrees_completed():
            return {
                'action': 'certificate',
                'enrollmentId': enrollment.id,
            }
        else:
            degree, step = enrollment.get_next_unlocked()
            return {
                'action': 'continue',
                'programId': enrollment.program.id,
                'degreeId': degree.id if degree else None,
                'stepId': step.id if step else None,
            }
