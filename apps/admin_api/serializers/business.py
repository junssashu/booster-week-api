from rest_framework import serializers

from apps.accounts.models import User
from apps.enrollments.models import Enrollment, Payment, PromoCode
from apps.sessions.models import SessionAttendance
from ._helpers import _map_camel_to_snake


class AdminUserSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    dateOfBirth = serializers.DateField(source='date_of_birth', allow_null=True, required=False)
    avatarUrl = serializers.CharField(source='avatar_url', allow_null=True, required=False)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'firstName', 'lastName', 'phone', 'email', 'role',
            'dateOfBirth', 'avatarUrl', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']


class AdminEnrollmentSerializer(serializers.ModelSerializer):
    programId = serializers.CharField(source='program_id')
    programName = serializers.CharField(source='program.name', read_only=True)
    userId = serializers.CharField(source='user_id')
    paymentType = serializers.CharField(source='payment_type')
    paymentStatus = serializers.CharField(source='payment_status')
    amountPaid = serializers.IntegerField(source='amount_paid')
    totalAmount = serializers.IntegerField(source='total_amount')
    enrollmentDate = serializers.DateTimeField(source='enrollment_date', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    mandataireId = serializers.CharField(
        source='mandataire_id', allow_null=True, required=False,
    )

    class Meta:
        model = Enrollment
        fields = [
            'id', 'programId', 'programName', 'userId', 'paymentType', 'paymentStatus',
            'amountPaid', 'totalAmount', 'enrollmentDate', 'mandataireId',
            'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'programName', 'enrollmentDate', 'createdAt', 'updatedAt']


class AdminPaymentSerializer(serializers.ModelSerializer):
    enrollmentId = serializers.CharField(source='enrollment_id')
    programName = serializers.CharField(source='enrollment.program.name', read_only=True)
    transactionRef = serializers.CharField(
        source='transaction_ref', allow_null=True, required=False,
    )
    mfTransactionId = serializers.CharField(
        source='mf_transaction_id', allow_null=True, required=False,
    )
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'enrollmentId', 'programName', 'amount', 'method', 'status',
            'transactionRef', 'mfTransactionId', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'programName', 'createdAt', 'updatedAt']


class AdminPromoCodeSerializer(serializers.ModelSerializer):
    discountPercent = serializers.IntegerField(source='discount_percent')
    maxUses = serializers.IntegerField(source='max_uses')
    currentUses = serializers.IntegerField(source='current_uses', read_only=True)
    isActive = serializers.BooleanField(source='is_active')
    expiresAt = serializers.DateTimeField(
        source='expires_at', allow_null=True, required=False,
    )
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'discountPercent', 'maxUses', 'currentUses',
            'isActive', 'expiresAt', 'createdAt',
        ]
        read_only_fields = ['id', 'currentUses', 'createdAt']


class AdminEnrollmentWriteSerializer(serializers.ModelSerializer):
    userId = serializers.CharField(source='user_id')
    programId = serializers.CharField(source='program_id')
    paymentType = serializers.CharField(source='payment_type')
    paymentStatus = serializers.CharField(source='payment_status')
    amountPaid = serializers.IntegerField(source='amount_paid')
    totalAmount = serializers.IntegerField(source='total_amount')
    mandataireId = serializers.CharField(
        source='mandataire_id', allow_null=True, required=False,
    )

    class Meta:
        model = Enrollment
        fields = [
            'id', 'userId', 'programId', 'paymentType', 'paymentStatus',
            'amountPaid', 'totalAmount', 'mandataireId',
        ]
        read_only_fields = ['id']


class AdminSessionAttendanceSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='user.first_name', read_only=True)
    lastName = serializers.CharField(source='user.last_name', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    joinedAt = serializers.DateTimeField(source='joined_at', read_only=True)

    class Meta:
        model = SessionAttendance
        fields = ['id', 'firstName', 'lastName', 'phone', 'joinedAt']
        read_only_fields = fields
