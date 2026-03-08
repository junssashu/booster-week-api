from rest_framework import serializers

from .models import Enrollment, Payment, PromoCode


class PaymentSerializer(serializers.ModelSerializer):
    transactionRef = serializers.CharField(source='transaction_ref', allow_null=True)

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'method', 'status', 'date', 'transactionRef']


class EnrollmentCreateSerializer(serializers.Serializer):
    programId = serializers.CharField()
    paymentType = serializers.ChoiceField(choices=['full', 'installment'])
    promoCode = serializers.CharField(max_length=10, required=False, allow_blank=True)


class EnrollmentListSerializer(serializers.ModelSerializer):
    programId = serializers.CharField(source='program_id')
    userId = serializers.CharField(source='user_id')
    paymentType = serializers.CharField(source='payment_type')
    paymentStatus = serializers.CharField(source='payment_status')
    amountPaid = serializers.IntegerField(source='amount_paid')
    totalAmount = serializers.IntegerField(source='total_amount')
    enrollmentDate = serializers.DateTimeField(source='enrollment_date')
    program = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ['id', 'programId', 'userId', 'paymentType', 'paymentStatus',
                  'amountPaid', 'totalAmount', 'enrollmentDate', 'program']

    def get_program(self, obj):
        return {
            'id': obj.program.id,
            'name': obj.program.name,
            'imageUrl': obj.program.image_url,
        }


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    programId = serializers.CharField(source='program_id')
    userId = serializers.CharField(source='user_id')
    paymentType = serializers.CharField(source='payment_type')
    paymentStatus = serializers.CharField(source='payment_status')
    amountPaid = serializers.IntegerField(source='amount_paid')
    totalAmount = serializers.IntegerField(source='total_amount')
    remainingAmount = serializers.SerializerMethodField()
    installmentAmount = serializers.SerializerMethodField()
    enrollmentDate = serializers.DateTimeField(source='enrollment_date')
    degreeAccess = serializers.SerializerMethodField()
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'programId', 'userId', 'paymentType', 'paymentStatus',
                  'amountPaid', 'totalAmount', 'remainingAmount', 'installmentAmount',
                  'enrollmentDate', 'degreeAccess', 'payments']

    def get_remainingAmount(self, obj):
        return obj.total_amount - obj.amount_paid

    def get_installmentAmount(self, obj):
        return obj.installment_amount

    def get_degreeAccess(self, obj):
        from apps.progress.models import StepProgress
        degrees = obj.program.degrees.all().order_by('order_index')
        result = []
        for d in degrees:
            accessible, lock_reason = obj.can_access_degree_detail(d)
            # Calculate degree completion percentage for the enrolled user
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
                'orderIndex': d.order_index,
                'accessible': accessible,
                'lockReason': lock_reason,
                'completionPercentage': completion_pct,
            })
        return result


class PaymentInitiateSerializer(serializers.Serializer):
    enrollmentId = serializers.CharField()
    amount = serializers.IntegerField(min_value=1)
    method = serializers.ChoiceField(choices=['orangeMoney', 'mtnMoney', 'wave'])
    phone = serializers.CharField()


class PaymentStatusSerializer(serializers.ModelSerializer):
    paymentId = serializers.CharField(source='id')
    transactionId = serializers.CharField(source='mf_transaction_id', allow_null=True)
    transactionRef = serializers.CharField(source='transaction_ref', allow_null=True)

    class Meta:
        model = Payment
        fields = ['paymentId', 'transactionId', 'status', 'amount', 'method', 'date', 'transactionRef']


class PromoCodeSerializer(serializers.ModelSerializer):
    discountPercent = serializers.IntegerField(source='discount_percent')
    maxUses = serializers.IntegerField(source='max_uses')
    currentUses = serializers.IntegerField(source='current_uses', read_only=True)
    expiresAt = serializers.DateTimeField(source='expires_at', allow_null=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    isValid = serializers.BooleanField(source='is_valid', read_only=True)

    class Meta:
        model = PromoCode
        fields = ['id', 'code', 'discountPercent', 'maxUses', 'currentUses', 'isValid', 'expiresAt', 'createdAt']


class PromoCodeValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=10)
