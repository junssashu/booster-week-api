from rest_framework import serializers

from apps.programs.models import (
    Program, Degree, Step, Asset, QCMQuestion, FormFieldDef,
    DegreeFile, PriseDeContact, PriseDeContactAsset,
)
from apps.core.storage import resolve_url


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _map_camel_to_snake(data, field_map):
    """Accept camelCase keys from the client and map them to snake_case."""
    mapped = {}
    for key, value in data.items():
        mapped[field_map.get(key, key)] = value
    return mapped


# ---------------------------------------------------------------------------
# Program
# ---------------------------------------------------------------------------

class AdminProgramSerializer(serializers.ModelSerializer):
    imageUrl = serializers.CharField(source='image_url', allow_blank=True, default='')
    durationWeeks = serializers.IntegerField(source='duration_weeks')
    presentationVideoUrl = serializers.CharField(
        source='presentation_video_url', allow_null=True, required=False,
    )
    isActive = serializers.BooleanField(source='is_active', default=True)
    degreeCount = serializers.SerializerMethodField(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Program
        fields = [
            'id', 'name', 'description', 'imageUrl', 'price',
            'durationWeeks', 'presentationVideoUrl', 'isActive',
            'degreeCount', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']

    def get_degreeCount(self, obj):
        return obj.degrees.count()

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'imageUrl': 'imageUrl',
                'durationWeeks': 'durationWeeks',
                'presentationVideoUrl': 'presentationVideoUrl',
                'isActive': 'isActive',
            })
        )


class AdminProgramDetailSerializer(AdminProgramSerializer):
    degrees = serializers.SerializerMethodField(read_only=True)

    class Meta(AdminProgramSerializer.Meta):
        fields = AdminProgramSerializer.Meta.fields + ['degrees']

    def get_degrees(self, obj):
        degrees = obj.degrees.all().order_by('order_index')
        return AdminDegreeSerializer(degrees, many=True).data


# ---------------------------------------------------------------------------
# Degree
# ---------------------------------------------------------------------------

class AdminDegreeSerializer(serializers.ModelSerializer):
    programId = serializers.CharField(source='program_id')
    orderIndex = serializers.IntegerField(source='order_index')
    stepCount = serializers.SerializerMethodField(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Degree
        fields = [
            'id', 'programId', 'title', 'description', 'orderIndex',
            'stepCount', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']

    def get_stepCount(self, obj):
        return obj.steps.count()

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'programId': 'programId',
                'orderIndex': 'orderIndex',
            })
        )


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------

class AdminStepSerializer(serializers.ModelSerializer):
    degreeId = serializers.CharField(source='degree_id')
    orderIndex = serializers.IntegerField(source='order_index')
    assetCount = serializers.SerializerMethodField(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Step
        fields = [
            'id', 'degreeId', 'title', 'description', 'orderIndex',
            'assetCount', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']

    def get_assetCount(self, obj):
        return obj.assets.count()

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'degreeId': 'degreeId',
                'orderIndex': 'orderIndex',
            })
        )


class AdminStepDetailSerializer(AdminStepSerializer):
    assets = serializers.SerializerMethodField(read_only=True)

    class Meta(AdminStepSerializer.Meta):
        fields = AdminStepSerializer.Meta.fields + ['assets']

    def get_assets(self, obj):
        assets = obj.assets.all().order_by('order_index')
        return AdminAssetSerializer(assets, many=True).data


class AdminDegreeDetailSerializer(AdminDegreeSerializer):
    steps = serializers.SerializerMethodField(read_only=True)
    files = serializers.SerializerMethodField(read_only=True)

    class Meta(AdminDegreeSerializer.Meta):
        fields = AdminDegreeSerializer.Meta.fields + ['steps', 'files']

    def get_steps(self, obj):
        steps = obj.steps.all().order_by('order_index')
        return AdminStepSerializer(steps, many=True).data

    def get_files(self, obj):
        files = obj.files.all().order_by('order_index')
        return AdminDegreeFileSerializer(files, many=True).data


# ---------------------------------------------------------------------------
# QCM Question
# ---------------------------------------------------------------------------

class AdminQCMQuestionSerializer(serializers.ModelSerializer):
    assetId = serializers.CharField(source='asset_id')
    correctIndex = serializers.IntegerField(source='correct_index')
    orderIndex = serializers.IntegerField(source='order_index')

    class Meta:
        model = QCMQuestion
        fields = ['id', 'assetId', 'question', 'options', 'correctIndex', 'orderIndex']
        read_only_fields = ['id']

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'assetId': 'assetId',
                'correctIndex': 'correctIndex',
                'orderIndex': 'orderIndex',
            })
        )


# ---------------------------------------------------------------------------
# Form Field
# ---------------------------------------------------------------------------

class AdminFormFieldSerializer(serializers.ModelSerializer):
    assetId = serializers.CharField(source='asset_id')
    selectOptions = serializers.JSONField(
        source='select_options', allow_null=True, required=False,
    )
    orderIndex = serializers.IntegerField(source='order_index')

    class Meta:
        model = FormFieldDef
        fields = ['id', 'assetId', 'label', 'type', 'required', 'selectOptions', 'orderIndex']

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'assetId': 'assetId',
                'selectOptions': 'selectOptions',
                'orderIndex': 'orderIndex',
            })
        )


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------

class AdminAssetSerializer(serializers.ModelSerializer):
    stepId = serializers.CharField(source='step_id')
    externalUrl = serializers.CharField(
        source='external_url', allow_null=True, required=False,
    )
    resolvedUrl = serializers.SerializerMethodField(read_only=True)
    orderIndex = serializers.IntegerField(source='order_index')
    passingScore = serializers.IntegerField(
        source='passing_score', default=70, required=False,
    )
    consigneText = serializers.CharField(
        source='consigne_text', allow_null=True, required=False,
    )
    questions = AdminQCMQuestionSerializer(many=True, read_only=True)
    formFields = AdminFormFieldSerializer(
        many=True, read_only=True, source='form_fields',
    )
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'stepId', 'type', 'title', 'description', 'externalUrl',
            'resolvedUrl', 'orderIndex', 'passingScore', 'consigneText',
            'questions', 'formFields', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']

    def get_resolvedUrl(self, obj):
        return resolve_url(obj.external_url) if obj.external_url else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Only include type-specific nested data
        if instance.type != 'qcm':
            data.pop('questions', None)
        if instance.type != 'form':
            data.pop('formFields', None)
        return data

    def to_internal_value(self, data):
        # Strip nested read-only keys before validation
        cleaned = {k: v for k, v in data.items() if k not in ('questions', 'formFields')}
        return super().to_internal_value(
            _map_camel_to_snake(cleaned, {
                'stepId': 'stepId',
                'externalUrl': 'externalUrl',
                'orderIndex': 'orderIndex',
                'passingScore': 'passingScore',
                'consigneText': 'consigneText',
            })
        )


# ---------------------------------------------------------------------------
# Degree File
# ---------------------------------------------------------------------------

class AdminDegreeFileSerializer(serializers.ModelSerializer):
    degreeId = serializers.CharField(source='degree_id')
    externalUrl = serializers.CharField(
        source='external_url', allow_null=True, required=False,
    )
    resolvedUrl = serializers.SerializerMethodField(read_only=True)
    orderIndex = serializers.IntegerField(source='order_index')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = DegreeFile
        fields = [
            'id', 'degreeId', 'type', 'title', 'description', 'externalUrl',
            'resolvedUrl', 'orderIndex', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']

    def get_resolvedUrl(self, obj):
        return resolve_url(obj.external_url) if obj.external_url else None

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'degreeId': 'degreeId',
                'externalUrl': 'externalUrl',
                'orderIndex': 'orderIndex',
            })
        )


# ---------------------------------------------------------------------------
# PriseDeContact Asset
# ---------------------------------------------------------------------------

class AdminPdcAssetSerializer(serializers.ModelSerializer):
    priseDeContactId = serializers.CharField(source='prise_de_contact_id')
    externalUrl = serializers.CharField(source='external_url')
    resolvedUrl = serializers.SerializerMethodField(read_only=True)
    orderIndex = serializers.IntegerField(source='order_index')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = PriseDeContactAsset
        fields = [
            'id', 'priseDeContactId', 'type', 'title', 'description',
            'externalUrl', 'resolvedUrl', 'orderIndex', 'createdAt',
        ]
        read_only_fields = ['id', 'createdAt']

    def get_resolvedUrl(self, obj):
        return resolve_url(obj.external_url) if obj.external_url else None

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'priseDeContactId': 'priseDeContactId',
                'externalUrl': 'externalUrl',
                'orderIndex': 'orderIndex',
            })
        )


# ---------------------------------------------------------------------------
# PriseDeContact
# ---------------------------------------------------------------------------

class AdminPriseDeContactSerializer(serializers.ModelSerializer):
    programId = serializers.CharField(
        source='program_id', allow_null=True, required=False,
    )
    degreeId = serializers.CharField(
        source='degree_id', allow_null=True, required=False,
    )
    stepId = serializers.CharField(
        source='step_id', allow_null=True, required=False,
    )
    orderIndex = serializers.IntegerField(source='order_index')
    assets = AdminPdcAssetSerializer(many=True, read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = PriseDeContact
        fields = [
            'id', 'programId', 'degreeId', 'stepId', 'title', 'description',
            'orderIndex', 'assets', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']

    def to_internal_value(self, data):
        cleaned = {k: v for k, v in data.items() if k != 'assets'}
        return super().to_internal_value(
            _map_camel_to_snake(cleaned, {
                'programId': 'programId',
                'degreeId': 'degreeId',
                'stepId': 'stepId',
                'orderIndex': 'orderIndex',
            })
        )


# ===================================================================
# Additional admin serializers (sessions, users, enrollments, etc.)
# ===================================================================

from apps.sessions.models import LiveReplaySession
from apps.accounts.models import User
from apps.enrollments.models import Enrollment, Payment, PromoCode
from apps.testimonies.models import Testimony
from apps.content.models import FAQItem, ContactInfo, ContactSubmission


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class AdminSessionSerializer(serializers.ModelSerializer):
    externalUrl = serializers.CharField(source='external_url')
    durationMinutes = serializers.IntegerField(source='duration_minutes')
    isLive = serializers.BooleanField(source='is_live')
    thumbnailUrl = serializers.CharField(
        source='thumbnail_url', allow_null=True, required=False,
    )
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = LiveReplaySession
        fields = [
            'id', 'title', 'description', 'externalUrl', 'date',
            'durationMinutes', 'isLive', 'thumbnailUrl',
            'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Enrollments
# ---------------------------------------------------------------------------

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

    class Meta:
        model = Enrollment
        fields = [
            'id', 'programId', 'programName', 'userId', 'userName',
            'paymentType', 'paymentStatus', 'amountPaid', 'totalAmount',
            'enrollmentDate', 'createdAt', 'updatedAt',
        ]
        read_only_fields = fields

    def get_userName(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Testimonies
# ---------------------------------------------------------------------------

class AdminTestimonySerializer(serializers.ModelSerializer):
    authorId = serializers.CharField(source='author_id', read_only=True)
    authorName = serializers.SerializerMethodField()
    videoUrl = serializers.CharField(source='video_url', read_only=True)
    likeCount = serializers.IntegerField(source='like_count', read_only=True)
    heartCount = serializers.IntegerField(source='heart_count', read_only=True)
    commentCount = serializers.IntegerField(source='comment_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Testimony
        fields = [
            'id', 'authorId', 'authorName', 'content', 'videoUrl',
            'likeCount', 'heartCount', 'commentCount',
            'createdAt', 'updatedAt',
        ]
        read_only_fields = fields

    def get_authorName(self, obj):
        return f'{obj.author.first_name} {obj.author.last_name}'


# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------

class AdminFAQSerializer(serializers.ModelSerializer):
    orderIndex = serializers.IntegerField(source='order_index')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = FAQItem
        fields = [
            'id', 'question', 'answer', 'orderIndex',
            'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']


# ---------------------------------------------------------------------------
# Contact Info (singleton)
# ---------------------------------------------------------------------------

class AdminContactInfoSerializer(serializers.ModelSerializer):
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ContactInfo
        fields = ['id', 'phone', 'email', 'whatsapp', 'updatedAt']
        read_only_fields = ['id', 'updatedAt']


# ---------------------------------------------------------------------------
# Contact Submissions
# ---------------------------------------------------------------------------

class AdminContactSubmissionSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = ContactSubmission
        fields = ['id', 'name', 'email', 'message', 'type', 'createdAt']
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Promo Codes
# ---------------------------------------------------------------------------

class AdminPromoCodeSerializer(serializers.ModelSerializer):
    creatorId = serializers.CharField(source='creator_id', read_only=True)
    creatorName = serializers.SerializerMethodField()
    discountPercent = serializers.IntegerField(source='discount_percent', read_only=True)
    maxUses = serializers.IntegerField(source='max_uses', read_only=True)
    currentUses = serializers.IntegerField(source='current_uses', read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    expiresAt = serializers.DateTimeField(source='expires_at', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    isValid = serializers.BooleanField(source='is_valid', read_only=True)

    class Meta:
        model = PromoCode
        fields = [
            'id', 'code', 'creatorId', 'creatorName',
            'discountPercent', 'maxUses', 'currentUses',
            'isActive', 'expiresAt', 'createdAt', 'isValid',
        ]
        read_only_fields = fields

    def get_creatorName(self, obj):
        return f'{obj.creator.first_name} {obj.creator.last_name}'
