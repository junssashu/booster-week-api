from rest_framework import serializers

from apps.accounts.models import User
from apps.enrollments.models import Enrollment, Payment, PromoCode
from ._helpers import _map_camel_to_snake


class AdminUserSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name', read_only=True)
    lastName = serializers.CharField(source='last_name', read_only=True)
    dateOfBirth = serializers.DateField(source='date_of_birth', read_only=True)
    avatarUrl = serializers.CharField(source='avatar_url', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'firstName', 'lastName', 'phone', 'email',
            'dateOfBirth', 'city', 'country', 'avatarUrl',
            'role', 'createdAt', 'updatedAt',
        ]
        read_only_fields = [
            'id', 'firstName', 'lastName', 'phone', 'email',
            'dateOfBirth', 'city', 'country', 'avatarUrl',
            'createdAt', 'updatedAt',
        ]


class AdminMandataireSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name', read_only=True)
    lastName = serializers.CharField(source='last_name', read_only=True)
    enrollmentCount = serializers.IntegerField(source='enrollment_count', read_only=True)
    totalRevenue = serializers.IntegerField(source='total_revenue', read_only=True, default=0)
    programs = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'firstName', 'lastName', 'phone', 'enrollmentCount', 'totalRevenue', 'programs']
        read_only_fields = fields

    def get_programs(self, obj):
        seen: set[str] = set()
        result: list[str] = []
        for enr in obj.mandated_enrollments.all():
            name = enr.program.name if enr.program else None
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result


class AdminEnrollmentSerializer(serializers.ModelSerializer):
    programId = serializers.CharField(source='program_id', read_only=True)
    programName = serializers.CharField(source='program.name', read_only=True)
    userId = serializers.CharField(source='user_id', read_only=True)
    userName = serializers.SerializerMethodField()
    paymentType = serializers.CharField(source='payment_type', read_only=True)
    paymentStatus = serializers.CharField(source='payment_status', read_only=True)
    amountPaid = serializers.IntegerField(source='amount_paid', read_only=True)
    totalAmount = serializers.IntegerField(source='total_amount', read_only=True)
    enrollmentDate = serializers.DateTimeField(source='enrollment_date', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    mandataire = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'id', 'programId', 'programName', 'userId', 'userName',
            'paymentType', 'paymentStatus', 'amountPaid', 'totalAmount',
            'enrollmentDate', 'createdAt', 'updatedAt', 'mandataire',
        ]
        read_only_fields = fields

    def get_userName(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'

    def get_mandataire(self, obj):
        if not obj.mandataire:
            return None
        return {
            'id': obj.mandataire.id,
            'firstName': obj.mandataire.first_name,
            'lastName': obj.mandataire.last_name,
            'phone': obj.mandataire.phone,
        }


class AdminPaymentSerializer(serializers.ModelSerializer):
    enrollmentId = serializers.CharField(source='enrollment_id', read_only=True)
    enrollmentProgramName = serializers.CharField(
        source='enrollment.program.name', read_only=True,
    )
    enrollmentUserName = serializers.SerializerMethodField()
    transactionRef = serializers.CharField(source='transaction_ref', read_only=True)
    mfTransactionId = serializers.CharField(source='mf_transaction_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'enrollmentId', 'enrollmentProgramName', 'enrollmentUserName',
            'amount', 'method', 'status', 'date',
            'transactionRef', 'mfTransactionId',
            'createdAt', 'updatedAt',
        ]
        read_only_fields = fields

    def get_enrollmentUserName(self, obj):
        user = obj.enrollment.user
        return f'{user.first_name} {user.last_name}'


class AdminPromoCodeSerializer(serializers.ModelSerializer):
    discountPercent = serializers.IntegerField(source='discount_percent')
    maxUses = serializers.IntegerField(source='max_uses')
    currentUses = serializers.IntegerField(source='current_uses', read_only=True)
    isActive = serializers.BooleanField(source='is_active', required=False)
    expiresAt = serializers.DateTimeField(source='expires_at', required=False, allow_null=True)
    creatorName = serializers.SerializerMethodField(read_only=True)
    redemptions = serializers.SerializerMethodField(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'discountPercent', 'maxUses', 'currentUses',
            'isActive', 'expiresAt', 'creatorName', 'redemptions', 'createdAt',
        ]
        read_only_fields = ['id', 'currentUses', 'creatorName', 'redemptions', 'createdAt']

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'discountPercent': 'discountPercent',
                'maxUses': 'maxUses',
                'isActive': 'isActive',
                'expiresAt': 'expiresAt',
            })
        )

    def get_creatorName(self, obj):
        return f'{obj.creator.first_name} {obj.creator.last_name}' if obj.creator else None

    def get_redemptions(self, obj):
        return [{
            'userName': f'{r.user.first_name} {r.user.last_name}',
            'programName': r.enrollment.program.name if r.enrollment else None,
            'discountApplied': r.discount_applied,
            'date': r.created_at,
        } for r in obj.redemptions.select_related('user', 'enrollment__program').all()]


