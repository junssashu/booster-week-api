from rest_framework import serializers

from .models import Enrollment, Payment


class PaymentSerializer(serializers.ModelSerializer):
    transactionRef = serializers.CharField(source='transaction_ref', allow_null=True)

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'method', 'status', 'date', 'transactionRef']


class EnrollmentCreateSerializer(serializers.Serializer):
    programId = serializers.CharField()
    paymentType = serializers.ChoiceField(choices=['full', 'installment'])


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
        degrees = obj.program.degrees.all().order_by('order_index')
        return [
            {
                'degreeId': d.id,
                'orderIndex': d.order_index,
                'accessible': obj.can_access_degree(d),
            }
            for d in degrees
        ]


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
