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
    numInstallments = serializers.IntegerField(source='num_installments', default=2)
    degreesPerInstallment = serializers.JSONField(source='degrees_per_installment', required=False, allow_null=True)
    completionThreshold = serializers.IntegerField(source='completion_threshold', default=70)
    whatsappCommunityUrl = serializers.CharField(
        source='whatsapp_community_url', allow_null=True, required=False
    )
    promotionDetails = serializers.CharField(
        source='promotion_details', allow_null=True, required=False
    )
    modulesText = serializers.CharField(
        source='modules_text', allow_null=True, required=False, allow_blank=True
    )
    previewAssets = serializers.JSONField(
        source='preview_assets', allow_null=True, required=False
    )
    degreeCount = serializers.SerializerMethodField(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Program
        fields = [
            'id', 'name', 'description', 'imageUrl', 'price',
            'durationWeeks', 'presentationVideoUrl', 'isActive',
            'numInstallments', 'degreesPerInstallment', 'completionThreshold',
            'whatsappCommunityUrl', 'promotionDetails', 'modulesText',
            'previewAssets', 'degreeCount', 'createdAt', 'updatedAt',
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
    programId = serializers.CharField(source='program_id', required=False)
    orderIndex = serializers.IntegerField(source='order_index', required=False)
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
    degreeId = serializers.CharField(source='degree_id', required=False)
    orderIndex = serializers.IntegerField(source='order_index', required=False)
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
    stepId = serializers.CharField(source='step_id', required=False)
    externalUrl = serializers.CharField(
        source='external_url', allow_null=True, required=False,
    )
    resolvedUrl = serializers.SerializerMethodField(read_only=True)
    orderIndex = serializers.IntegerField(source='order_index', required=False)
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

from apps.sessions.models import LiveReplaySession, SessionAttendance
from apps.accounts.models import User
from apps.enrollments.models import Enrollment, Payment, PromoCode
from apps.testimonies.models import Testimony, TestimonyComment
from apps.content.models import FAQItem, ContactInfo, ContactSubmission, AppSettings


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
    attendanceCount = serializers.IntegerField(source='attendance_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = LiveReplaySession
        fields = [
            'id', 'title', 'description', 'externalUrl', 'date',
            'durationMinutes', 'isLive', 'thumbnailUrl',
            'attendanceCount', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['id', 'attendanceCount', 'createdAt', 'updatedAt']

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'externalUrl': 'externalUrl',
                'durationMinutes': 'durationMinutes',
                'isLive': 'isLive',
                'thumbnailUrl': 'thumbnailUrl',
            })
        )


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
# Testimony Comments
# ---------------------------------------------------------------------------

class AdminTestimonyCommentSerializer(serializers.ModelSerializer):
    authorName = serializers.SerializerMethodField()
    testimonyId = serializers.CharField(source='testimony_id')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = TestimonyComment
        fields = ['id', 'content', 'authorName', 'testimonyId', 'createdAt']
        read_only_fields = fields

    def get_authorName(self, obj):
        return f'{obj.author.first_name} {obj.author.last_name}'


# ---------------------------------------------------------------------------
# Testimonies
# ---------------------------------------------------------------------------

class AdminTestimonySerializer(serializers.ModelSerializer):
    authorId = serializers.CharField(source='author_id')
    authorName = serializers.SerializerMethodField(read_only=True)
    videoUrl = serializers.CharField(
        source='video_url', required=False, allow_blank=True, allow_null=True,
    )
    content = serializers.CharField(
        required=False, allow_blank=True, default='',
    )
    likeCount = serializers.IntegerField(source='like_count', read_only=True)
    heartCount = serializers.IntegerField(source='heart_count', read_only=True)
    commentCount = serializers.IntegerField(source='comment_count', read_only=True)
    comments = AdminTestimonyCommentSerializer(many=True, read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Testimony
        fields = [
            'id', 'authorId', 'authorName', 'content', 'videoUrl',
            'likeCount', 'heartCount', 'commentCount', 'comments',
            'createdAt', 'updatedAt',
        ]
        read_only_fields = [
            'id', 'authorName', 'likeCount', 'heartCount',
            'commentCount', 'comments', 'createdAt', 'updatedAt',
        ]

    def get_authorName(self, obj):
        return f'{obj.author.first_name} {obj.author.last_name}'

    def validate(self, data):
        content = data.get('content', '')
        video_url = data.get('video_url', '')
        if not content and not video_url:
            raise serializers.ValidationError(
                'Au moins un contenu texte ou une URL video est requis.'
            )
        author_id = data.get('author_id')
        if author_id and not User.objects.filter(id=author_id).exists():
            raise serializers.ValidationError({'authorId': 'Utilisateur introuvable.'})
        return data

    def create(self, validated_data):
        return Testimony.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.content = validated_data.get('content', instance.content)
        instance.video_url = validated_data.get('video_url', instance.video_url)
        if 'author_id' in validated_data:
            instance.author_id = validated_data['author_id']
        instance.save()
        return instance


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

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'orderIndex': 'orderIndex',
            })
        )


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
        fields = ['id', 'code', 'discountPercent', 'maxUses', 'currentUses',
                  'isActive', 'expiresAt', 'creatorName', 'redemptions', 'createdAt']
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


# ---------------------------------------------------------------------------
# Enrollment Write (for create/update)
# ---------------------------------------------------------------------------

class AdminEnrollmentWriteSerializer(serializers.ModelSerializer):
    userId = serializers.CharField(source='user_id')
    programId = serializers.CharField(source='program_id')
    paymentType = serializers.CharField(source='payment_type')
    paymentStatus = serializers.CharField(source='payment_status', required=False)
    amountPaid = serializers.IntegerField(source='amount_paid', required=False)
    totalAmount = serializers.IntegerField(source='total_amount')
    mandataireId = serializers.CharField(source='mandataire_id', required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Enrollment
        fields = ['userId', 'programId', 'paymentType', 'paymentStatus', 'amountPaid', 'totalAmount', 'mandataireId']

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


# ---------------------------------------------------------------------------
# Session Attendance
# ---------------------------------------------------------------------------

class AdminSessionAttendanceSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='user.first_name')
    lastName = serializers.CharField(source='user.last_name')
    phone = serializers.CharField(source='user.phone')
    joinedAt = serializers.DateTimeField(source='joined_at')

    class Meta:
        model = SessionAttendance
        fields = ['id', 'firstName', 'lastName', 'phone', 'joinedAt']


# ---------------------------------------------------------------------------
# App Settings (singleton)
# ---------------------------------------------------------------------------

class AdminAppSettingsSerializer(serializers.ModelSerializer):
    backgroundMusicUrl = serializers.URLField(source='background_music_url', required=False, allow_blank=True)
    presentationVideoUrl = serializers.URLField(source='presentation_video_url', required=False, allow_blank=True)
    appName = serializers.CharField(source='app_name', required=False)
    socialLinks = serializers.JSONField(source='social_links', required=False)
    footerTagline = serializers.CharField(source='footer_tagline', required=False)
    paymentExpiryMinutes = serializers.IntegerField(source='payment_expiry_minutes', required=False, min_value=1, max_value=120)

    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = AppSettings
        fields = ['backgroundMusicUrl', 'presentationVideoUrl', 'appName', 'socialLinks', 'footerTagline', 'paymentExpiryMinutes', 'updatedAt']
        read_only_fields = ['updatedAt']

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {
                'backgroundMusicUrl': 'backgroundMusicUrl',
                'presentationVideoUrl': 'presentationVideoUrl',
                'appName': 'appName',
                'socialLinks': 'socialLinks',
                'footerTagline': 'footerTagline',
                'paymentExpiryMinutes': 'paymentExpiryMinutes',
            })
        )


# ---------------------------------------------------------------------------
# Progress Tracking
# ---------------------------------------------------------------------------

from apps.progress.models import StepProgress, QCMAttempt, FormSubmission, AssetCompletion


class AdminStepProgressSerializer(serializers.ModelSerializer):
    stepId = serializers.CharField(source='step.id')
    stepTitle = serializers.CharField(source='step.title')
    completionPercentage = serializers.IntegerField(source='completion_percentage')
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = StepProgress
        fields = ['stepId', 'stepTitle', 'status', 'completionPercentage', 'updatedAt']


class AdminQCMAttemptSerializer(serializers.ModelSerializer):
    assetTitle = serializers.CharField(source='asset.title')
    attemptedAt = serializers.DateTimeField(source='attempted_at', read_only=True)

    class Meta:
        model = QCMAttempt
        fields = ['id', 'assetTitle', 'score', 'passed', 'attemptedAt']


class AdminFormSubmissionSerializer(serializers.ModelSerializer):
    assetTitle = serializers.CharField(source='asset.title')
    submittedAt = serializers.DateTimeField(source='submitted_at', read_only=True)

    class Meta:
        model = FormSubmission
        fields = ['id', 'assetTitle', 'responses', 'submittedAt']
