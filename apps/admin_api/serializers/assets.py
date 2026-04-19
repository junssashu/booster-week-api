from rest_framework import serializers

from apps.programs.models import Asset, QCMQuestion, FormFieldDef, DegreeFile
from apps.core.storage import resolve_url
from ._helpers import _map_camel_to_snake


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
        if instance.type != 'qcm':
            data.pop('questions', None)
        if instance.type != 'form':
            data.pop('formFields', None)
        return data

    def to_internal_value(self, data):
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
