from rest_framework import serializers


class EnrollmentCreateSerializer(serializers.Serializer):
    programId = serializers.CharField()
    paymentType = serializers.ChoiceField(choices=['full', 'installment'])
    promoCode = serializers.CharField(max_length=10, required=False, allow_blank=True)
    mandataireId = serializers.CharField(required=False, allow_null=True, allow_blank=True)
