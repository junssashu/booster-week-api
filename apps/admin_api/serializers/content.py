from rest_framework import serializers

from apps.programs.models import PriseDeContact, PriseDeContactAsset
from apps.sessions.models import LiveReplaySession
from apps.content.models import FAQItem, ContactInfo, ContactSubmission, AppSettings
from apps.core.storage import resolve_url
from ._helpers import _map_camel_to_snake


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


class AdminSessionSerializer(serializers.ModelSerializer):
    externalUrl = serializers.CharField(source='external_url')
    durationMinutes = serializers.IntegerField(source='duration_minutes')
    isLive = serializers.BooleanField(source='is_live')
    thumbnailUrl = serializers.CharField(
        source='thumbnail_url', allow_null=True, required=False,
    )
    programId = serializers.CharField(source='program_id', allow_null=True, required=False)
    attendanceCount = serializers.IntegerField(source='attendance_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = LiveReplaySession
        fields = [
            'id', 'title', 'description', 'externalUrl', 'date',
            'durationMinutes', 'isLive', 'thumbnailUrl', 'programId',
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
                'programId': 'programId',
            })
        )


class AdminFAQSerializer(serializers.ModelSerializer):
    orderIndex = serializers.IntegerField(source='order_index')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = FAQItem
        fields = ['id', 'question', 'answer', 'orderIndex', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'createdAt', 'updatedAt']

    def to_internal_value(self, data):
        return super().to_internal_value(
            _map_camel_to_snake(data, {'orderIndex': 'orderIndex'})
        )


class AdminContactInfoSerializer(serializers.ModelSerializer):
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ContactInfo
        fields = ['id', 'phone', 'email', 'whatsapp', 'updatedAt']
        read_only_fields = ['id', 'updatedAt']


class AdminContactSubmissionSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = ContactSubmission
        fields = ['id', 'name', 'email', 'message', 'type', 'createdAt']
        read_only_fields = fields


class AdminAppSettingsSerializer(serializers.ModelSerializer):
    backgroundMusicUrl = serializers.URLField(source='background_music_url', required=False, allow_blank=True)
    presentationVideoUrl = serializers.URLField(source='presentation_video_url', required=False, allow_blank=True)
    appName = serializers.CharField(source='app_name', required=False)
    socialLinks = serializers.JSONField(source='social_links', required=False)
    footerTagline = serializers.CharField(source='footer_tagline', required=False)
    paymentExpiryMinutes = serializers.IntegerField(
        source='payment_expiry_minutes', required=False, min_value=1, max_value=120,
    )
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = AppSettings
        fields = [
            'backgroundMusicUrl', 'presentationVideoUrl', 'appName',
            'socialLinks', 'footerTagline', 'paymentExpiryMinutes', 'updatedAt',
        ]
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
