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
