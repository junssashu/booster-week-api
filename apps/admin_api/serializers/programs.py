from rest_framework import serializers

from apps.programs.models import Program, Degree, Step
from ._helpers import _map_camel_to_snake
from .assets import AdminAssetSerializer, AdminDegreeFileSerializer


class AdminProgramSerializer(serializers.ModelSerializer):
    imageUrl = serializers.CharField(source='image_url', allow_blank=True, default='')
    durationWeeks = serializers.IntegerField(source='duration_weeks')
    presentationVideoUrl = serializers.CharField(
        source='presentation_video_url', allow_null=True, allow_blank=True, required=False,
    )
    isActive = serializers.BooleanField(source='is_active', default=True)
    numInstallments = serializers.IntegerField(source='num_installments', default=2)
    degreesPerInstallment = serializers.JSONField(source='degrees_per_installment', required=False, allow_null=True)
    completionThreshold = serializers.IntegerField(source='completion_threshold', default=70)
    whatsappCommunityUrl = serializers.CharField(
        source='whatsapp_community_url', allow_null=True, allow_blank=True, required=False
    )
    promotionDetails = serializers.CharField(
        source='promotion_details', allow_null=True, allow_blank=True, required=False
    )
    modulesText = serializers.CharField(
        source='modules_text', allow_null=True, required=False, allow_blank=True
    )
    previewAssets = serializers.JSONField(
        source='preview_assets', allow_null=True, required=False
    )
    enrollmentFormAssetId = serializers.CharField(
        source='enrollment_form_asset_id', allow_null=True, required=False, allow_blank=True
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
            'previewAssets', 'enrollmentFormAssetId', 'degreeCount', 'createdAt', 'updatedAt',
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
