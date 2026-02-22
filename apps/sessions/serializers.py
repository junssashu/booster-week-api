from rest_framework import serializers

from .models import LiveReplaySession


class SessionSerializer(serializers.ModelSerializer):
    externalUrl = serializers.CharField(source='external_url')
    durationMinutes = serializers.IntegerField(source='duration_minutes')
    isLive = serializers.BooleanField(source='is_live')
    thumbnailUrl = serializers.CharField(source='thumbnail_url', allow_null=True)

    class Meta:
        model = LiveReplaySession
        fields = ['id', 'title', 'description', 'externalUrl', 'date',
                  'durationMinutes', 'isLive', 'thumbnailUrl']
