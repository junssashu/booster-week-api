from rest_framework import serializers

from apps.core.storage import resolve_url
from .models import Testimony, TestimonyComment


class TestimonySerializer(serializers.ModelSerializer):
    authorId = serializers.CharField(source='author_id')
    authorName = serializers.SerializerMethodField()
    videoUrl = serializers.SerializerMethodField()
    likeCount = serializers.IntegerField(source='like_count')
    commentCount = serializers.IntegerField(source='comment_count')
    createdAt = serializers.DateTimeField(source='created_at')
    userHasLiked = serializers.SerializerMethodField()

    class Meta:
        model = Testimony
        fields = ['id', 'authorId', 'authorName', 'content', 'videoUrl',
                  'createdAt', 'likeCount', 'commentCount', 'userHasLiked']

    def get_authorName(self, obj):
        return f'{obj.author.first_name} {obj.author.last_name}'

    def get_videoUrl(self, obj):
        if not obj.video_url:
            return None
        return resolve_url(obj.video_url)

    def get_userHasLiked(self, obj):
        user = self.context.get('user')
        if not user:
            return None
        return obj.reactions.filter(user=user, reaction_type='like').exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Remove user reaction fields if no authenticated user
        if data.get('userHasLiked') is None:
            data.pop('userHasLiked', None)
        return data


class TestimonyCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=5000, required=False, allow_blank=True, default='')
    videoUrl = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        content = data.get('content', '').strip()
        video_url = data.get('videoUrl', '').strip() if data.get('videoUrl') else ''
        if not content and not video_url:
            raise serializers.ValidationError('At least one of content or videoUrl is required.')
        return data


class CommentSerializer(serializers.ModelSerializer):
    testimonyId = serializers.CharField(source='testimony_id')
    authorId = serializers.CharField(source='author_id')
    authorName = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at')

    class Meta:
        model = TestimonyComment
        fields = ['id', 'testimonyId', 'authorId', 'authorName', 'content', 'createdAt']

    def get_authorName(self, obj):
        return f'{obj.author.first_name} {obj.author.last_name}'


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=2000)
