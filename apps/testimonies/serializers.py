from rest_framework import serializers

from .models import Testimony, TestimonyComment


class TestimonySerializer(serializers.ModelSerializer):
    authorId = serializers.CharField(source='author_id')
    authorName = serializers.SerializerMethodField()
    likeCount = serializers.IntegerField(source='like_count')
    heartCount = serializers.IntegerField(source='heart_count')
    commentCount = serializers.IntegerField(source='comment_count')
    createdAt = serializers.DateTimeField(source='created_at')
    userHasLiked = serializers.SerializerMethodField()
    userHasHearted = serializers.SerializerMethodField()

    class Meta:
        model = Testimony
        fields = ['id', 'authorId', 'authorName', 'content', 'createdAt',
                  'likeCount', 'heartCount', 'commentCount',
                  'userHasLiked', 'userHasHearted']

    def get_authorName(self, obj):
        return f'{obj.author.first_name} {obj.author.last_name}'

    def get_userHasLiked(self, obj):
        user = self.context.get('user')
        if not user:
            return None
        return obj.reactions.filter(user=user, reaction_type='like').exists()

    def get_userHasHearted(self, obj):
        user = self.context.get('user')
        if not user:
            return None
        return obj.reactions.filter(user=user, reaction_type='heart').exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Remove user reaction fields if no authenticated user
        if data.get('userHasLiked') is None:
            data.pop('userHasLiked', None)
            data.pop('userHasHearted', None)
        return data


class TestimonyCreateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=10, max_length=5000)


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
