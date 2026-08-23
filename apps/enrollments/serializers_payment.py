from rest_framework import serializers

from .models import Payment, PromoCode


class PaymentSerializer(serializers.ModelSerializer):
    transactionRef = serializers.CharField(source='transaction_ref', allow_null=True)

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'method', 'status', 'date', 'transactionRef']


class PaymentInitiateSerializer(serializers.Serializer):
    enrollmentId = serializers.CharField()
    amount = serializers.IntegerField(min_value=1)
    method = serializers.ChoiceField(choices=['orangeMoney', 'mtnMoney', 'wave'], default='orangeMoney', required=False)
    phone = serializers.CharField(required=False, allow_blank=True, default='')


class PaymentStatusSerializer(serializers.ModelSerializer):
    paymentId = serializers.CharField(source='id')
    transactionId = serializers.CharField(source='mf_transaction_id', allow_null=True)
    transactionRef = serializers.CharField(source='transaction_ref', allow_null=True)
    paymentUrl = serializers.URLField(source='payment_url', allow_null=True, required=False)

    class Meta:
        model = Payment
        fields = ['paymentId', 'transactionId', 'status', 'amount', 'method', 'date', 'transactionRef', 'paymentUrl']


class PaymentHistorySerializer(serializers.Serializer):
    id = serializers.CharField()
    amount = serializers.IntegerField()
    method = serializers.CharField()
    status = serializers.CharField()
    date = serializers.DateTimeField(source='created_at')
    transactionRef = serializers.CharField(source='mf_transaction_id', default='')
    enrollmentId = serializers.CharField(source='enrollment_id')
    programId = serializers.SerializerMethodField()
    programName = serializers.SerializerMethodField()
    programImageUrl = serializers.SerializerMethodField()
    paymentUrl = serializers.CharField(source='payment_url', allow_null=True, required=False)

    def get_programId(self, obj):
        return obj.enrollment.program.id if obj.enrollment else None

    def get_programName(self, obj):
        return obj.enrollment.program.name if obj.enrollment and obj.enrollment.program else ''

    def get_programImageUrl(self, obj):
        return obj.enrollment.program.image_url if obj.enrollment and obj.enrollment.program else ''


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
