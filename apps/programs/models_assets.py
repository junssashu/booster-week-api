import uuid

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from apps.core.utils import generate_prefixed_id
from .models_programs import Program, Degree, Step


ASSET_TYPES = [
    ('pdf', 'PDF'), ('audio', 'Audio'), ('video', 'Video'), ('qcm', 'QCM'),
    ('form', 'Form'), ('consigne', 'Consigne'), ('image', 'Image'),
]


class Asset(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    # step is nullable so that standalone enrollment form assets can exist without a step
    step = models.ForeignKey(
        Step, on_delete=models.CASCADE, null=True, blank=True, related_name='assets',
    )
    # program is set for standalone form assets (enrollment forms)
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, null=True, blank=True, related_name='form_assets',
    )
    type = models.CharField(max_length=20, choices=ASSET_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    external_url = models.TextField(null=True, blank=True)
    order_index = models.IntegerField(default=0)
    passing_score = models.IntegerField(default=70)
    consigne_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assets'
        ordering = ['order_index']
        indexes = [
            models.Index(fields=['step']),
            models.Index(fields=['type']),
            models.Index(fields=['program']),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('asset')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.type}: {self.title}'


class QCMQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    options = models.JSONField()
    correct_index = models.IntegerField()
    order_index = models.IntegerField()

    class Meta:
        db_table = 'qcm_questions'
        ordering = ['order_index']
        unique_together = [['asset', 'order_index']]
        indexes = [models.Index(fields=['asset'])]


class FormFieldDef(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='form_fields')
    label = models.TextField()
    type = models.CharField(max_length=20)  # text, email, phone, textarea, select
    required = models.BooleanField(default=False)
    select_options = models.JSONField(null=True, blank=True)
    order_index = models.IntegerField()

    class Meta:
        db_table = 'form_fields'
        ordering = ['order_index']
        unique_together = [['asset', 'order_index']]
        indexes = [models.Index(fields=['asset'])]


class PriseDeContact(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, null=True, blank=True,
        related_name='prises_de_contact',
    )
    degree = models.ForeignKey(
        Degree, on_delete=models.CASCADE, null=True, blank=True,
        related_name='prises_de_contact',
    )
    step = models.ForeignKey(
        Step, on_delete=models.CASCADE, null=True, blank=True,
        related_name='prises_de_contact',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    order_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_index']
        db_table = 'programs_prisedecontact'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"pdc_{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        parents = [self.program, self.degree, self.step]
        non_null = [p for p in parents if p is not None]
        if len(non_null) != 1:
            raise ValidationError('Exactly one of program, degree, or step must be set.')

    def __str__(self):
        return self.title


@receiver(pre_delete, sender=Asset)
def cleanup_asset_progress(sender, instance, **kwargs):
    from apps.progress.models import AssetCompletion, QCMAttempt, FormSubmission
    AssetCompletion.objects.filter(asset=instance).delete()
    QCMAttempt.objects.filter(asset=instance).delete()
    FormSubmission.objects.filter(asset=instance).delete()


class PriseDeContactAsset(models.Model):
    ASSET_TYPES = [
        ('video', 'Video'), ('audio', 'Audio'), ('pdf', 'PDF'), ('image', 'Image'),
    ]

    id = models.CharField(max_length=50, primary_key=True)
    prise_de_contact = models.ForeignKey(
        PriseDeContact, on_delete=models.CASCADE, related_name='assets',
    )
    type = models.CharField(max_length=10, choices=ASSET_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    external_url = models.TextField()
    order_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order_index']
        db_table = 'programs_prisedecontactasset'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"pdca_{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.type}: {self.title}'
