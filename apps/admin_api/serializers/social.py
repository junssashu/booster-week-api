from rest_framework import serializers

from apps.accounts.models import User
from apps.testimonies.models import Testimony, TestimonyComment
from apps.progress.models import StepProgress, QCMAttempt, FormSubmission


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


class AdminTestimonySerializer(serializers.ModelSerializer):
    authorId = serializers.CharField(source='author_id')
    authorName = serializers.SerializerMethodField(read_only=True)
    videoUrl = serializers.CharField(
        source='video_url', required=False, allow_blank=True, allow_null=True,
    )
    content = serializers.CharField(required=False, allow_blank=True, default='')
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


class AdminFormSubmissionRowSerializer(serializers.ModelSerializer):
    submittedAt = serializers.DateTimeField(source='submitted_at', read_only=True)
    userName = serializers.SerializerMethodField()
    userPhone = serializers.SerializerMethodField()
    programTitle = serializers.SerializerMethodField()
    formTitle = serializers.CharField(source='asset.title', read_only=True)
    responseCount = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = FormSubmission
        fields = ['id', 'submittedAt', 'type', 'userName', 'userPhone',
                  'programTitle', 'formTitle', 'responseCount']

    def get_userName(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'.strip()

    def get_userPhone(self, obj):
        return obj.user.phone or ''

    def get_type(self, obj):
        enrollment_ids = self.context.get('enrollment_asset_ids', set())
        return 'enrollment' if obj.asset_id in enrollment_ids else 'in-course'

    def get_programTitle(self, obj):
        enrollment_ids = self.context.get('enrollment_asset_ids', set())
        if obj.asset_id in enrollment_ids:
            return obj.asset.program.name if obj.asset.program else ''
        if obj.asset.step and obj.asset.step.degree and obj.asset.step.degree.program:
            return obj.asset.step.degree.program.name
        return ''

    def get_responseCount(self, obj):
        return len(obj.responses) if isinstance(obj.responses, list) else 0


class AdminFormSubmissionDetailSerializer(serializers.ModelSerializer):
    submittedAt = serializers.DateTimeField(source='submitted_at', read_only=True)
    userName = serializers.SerializerMethodField()
    formTitle = serializers.CharField(source='asset.title', read_only=True)
    responses = serializers.SerializerMethodField()

    class Meta:
        model = FormSubmission
        fields = ['id', 'submittedAt', 'userName', 'formTitle', 'responses']

    def get_userName(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'.strip()

    def get_responses(self, obj):
        field_map = {
            f.id: f.label
            for f in obj.asset.form_fields.all()
        }
        return [
            {
                'fieldLabel': field_map.get(r.get('fieldId', ''), r.get('fieldId', '')),
                'value': r.get('value', ''),
            }
            for r in (obj.responses or [])
            if isinstance(r, dict)
        ]
