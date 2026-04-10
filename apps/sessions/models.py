from django.db import models

from apps.core.utils import generate_prefixed_id


class LiveReplaySession(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    external_url = models.TextField()
    date = models.DateTimeField()
    duration_minutes = models.IntegerField()
    is_live = models.BooleanField()
    thumbnail_url = models.TextField(null=True, blank=True)
    program = models.ForeignKey(
        'programs.Program',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sessions',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'live_replay_sessions'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['is_live']),
            models.Index(fields=['-date']),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            prefix = 'live' if self.is_live else 'replay'
            self.id = generate_prefixed_id(prefix)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class SessionAttendance(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    session = models.ForeignKey(LiveReplaySession, on_delete=models.CASCADE, related_name='attendances')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='session_attendances')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'session_attendances'
        unique_together = [['session', 'user']]
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['user']),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('att')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} joined {self.session}"
