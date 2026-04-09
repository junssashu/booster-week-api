import uuid

from django.db import models


class ContactSubmission(models.Model):
    TYPE_CHOICES = [
        ('contact', 'Contact'),
        ('bug', 'Bug Report'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True)
    message = models.TextField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='contact')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contact_submissions'
        ordering = ['-created_at']


class FAQItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    answer = models.TextField()
    order_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'faq_items'
        ordering = ['order_index']
        indexes = [models.Index(fields=['order_index'])]


class ContactInfo(models.Model):
    id = models.IntegerField(primary_key=True, default=1)
    phone = models.CharField(max_length=20)
    email = models.EmailField(max_length=255)
    whatsapp = models.CharField(max_length=20)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_info'


class AppSettings(models.Model):
    id = models.IntegerField(primary_key=True, default=1)
    background_music_url = models.URLField(max_length=500, blank=True, default='')
    presentation_video_url = models.URLField(max_length=500, blank=True, default='')
    app_name = models.CharField(max_length=100, default='Booster Week')
    social_links = models.JSONField(default=dict, blank=True)
    footer_tagline = models.TextField(default='Elevez vos vibrations et transformez votre quotidien.')
    payment_expiry_minutes = models.IntegerField(default=15, help_text='Minutes before a pending payment expires')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_settings'
        verbose_name_plural = 'App Settings'

    def __str__(self):
        return f'App Settings (v{self.updated_at})'
