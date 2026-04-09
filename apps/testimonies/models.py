import uuid

from django.db import models

from apps.accounts.models import User
from apps.core.utils import generate_prefixed_id


class Testimony(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimonies')
    content = models.TextField(blank=True, default='')
    video_url = models.TextField(null=True, blank=True)
    like_count = models.IntegerField(default=0)
    heart_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'testimonies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['-like_count']),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('test')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Testimony by {self.author} ({self.id})'


class TestimonyReaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    testimony = models.ForeignKey(Testimony, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimony_reactions')
    reaction_type = models.CharField(max_length=10)  # like, heart
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'testimony_reactions'
        unique_together = [['testimony', 'user', 'reaction_type']]
        indexes = [models.Index(fields=['testimony'])]


class TestimonyComment(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    testimony = models.ForeignKey(Testimony, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimony_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'testimony_comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['testimony']),
            models.Index(fields=['author']),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('com')
        super().save(*args, **kwargs)


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver([post_save, post_delete], sender=TestimonyComment)
def update_testimony_comment_count(sender, instance, **kwargs):
    testimony = instance.testimony
    testimony.comment_count = testimony.comments.count()
    testimony.save(update_fields=['comment_count'])


@receiver([post_save, post_delete], sender=TestimonyReaction)
def update_testimony_reaction_counts(sender, instance, **kwargs):
    testimony = instance.testimony
    testimony.like_count = testimony.reactions.filter(reaction_type='like').count()
    testimony.heart_count = testimony.reactions.filter(reaction_type='heart').count()
    testimony.save(update_fields=['like_count', 'heart_count'])
