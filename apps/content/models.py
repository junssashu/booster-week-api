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
