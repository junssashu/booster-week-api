from rest_framework import serializers

from .models import LiveReplaySession, SessionAttendance


class SessionSerializer(serializers.ModelSerializer):
    externalUrl = serializers.CharField(source='external_url')
    durationMinutes = serializers.IntegerField(source='duration_minutes')
    isLive = serializers.BooleanField(source='is_live')
    thumbnailUrl = serializers.CharField(source='thumbnail_url', allow_null=True)
    programId = serializers.CharField(source='program_id', allow_null=True, read_only=True)
    hasJoined = serializers.SerializerMethodField()
    attendeeCount = serializers.SerializerMethodField()

    class Meta:
        model = LiveReplaySession
        fields = ['id', 'title', 'description', 'externalUrl', 'date',
                  'durationMinutes', 'isLive', 'thumbnailUrl', 'programId',
                  'hasJoined', 'attendeeCount']

    def get_hasJoined(self, obj):
        user = self.context.get('user')
        if not user or not user.is_authenticated:
            return False
        return obj.attendances.filter(user=user).exists()

    def get_attendeeCount(self, obj):
        return obj.attendances.count()


class SessionAttendanceSerializer(serializers.ModelSerializer):
    joinedAt = serializers.DateTimeField(source='joined_at')

    class Meta:
        model = SessionAttendance
        fields = ['id', 'joinedAt']
