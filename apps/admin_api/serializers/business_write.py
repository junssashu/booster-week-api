from rest_framework import serializers

from apps.accounts.models import User
from apps.enrollments.models import Enrollment
from apps.sessions.models import SessionAttendance
from ._helpers import _map_camel_to_snake


class AdminEnrollmentWriteSerializer(serializers.ModelSerializer):
    userId = serializers.CharField(source='user_id')
    programId = serializers.CharField(source='program_id')
    paymentType = serializers.CharField(source='payment_type')
    paymentStatus = serializers.CharField(source='payment_status', required=False)
    amountPaid = serializers.IntegerField(source='amount_paid', required=False)
    totalAmount = serializers.IntegerField(source='total_amount')
    mandataireId = serializers.CharField(
        source='mandataire_id', required=False, allow_null=True, allow_blank=True,
    )

    class Meta:
        model = Enrollment
        fields = [
            'userId', 'programId', 'paymentType', 'paymentStatus',
            'amountPaid', 'totalAmount', 'mandataireId',
        ]

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'userId': 'userId',
                'programId': 'programId',
                'paymentType': 'paymentType',
                'paymentStatus': 'paymentStatus',
                'amountPaid': 'amountPaid',
                'totalAmount': 'totalAmount',
                'mandataireId': 'mandataireId',
            })
        )

    def validate_mandataireId(self, value):
        if value in (None, ''):
            return value
        if not User.objects.filter(id=value, is_mandataire=True).exists():
            raise serializers.ValidationError('User is not a designated mandataire.')
        return value


class AdminSessionAttendanceSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='user.first_name')
    lastName = serializers.CharField(source='user.last_name')
    phone = serializers.CharField(source='user.phone')
    joinedAt = serializers.DateTimeField(source='joined_at')

    class Meta:
        model = SessionAttendance
        fields = ['id', 'firstName', 'lastName', 'phone', 'joinedAt']
