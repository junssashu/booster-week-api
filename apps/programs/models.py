import uuid

from django.db import models

from apps.core.utils import generate_prefixed_id


class Program(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    image_url = models.TextField()
    price = models.IntegerField()
    duration_weeks = models.IntegerField()
    presentation_video_url = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'programs'
        indexes = [models.Index(fields=['is_active'])]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('prog')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Degree(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='degrees')
    title = models.CharField(max_length=255)
    description = models.TextField()
    order_index = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'degrees'
        ordering = ['order_index']
        unique_together = [['program', 'order_index']]
        indexes = [models.Index(fields=['program'])]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('deg')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Step(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE, related_name='steps')
    title = models.CharField(max_length=255)
    description = models.TextField()
    order_index = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'steps'
        ordering = ['order_index']
        unique_together = [['degree', 'order_index']]
        indexes = [models.Index(fields=['degree'])]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('step')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


ASSET_TYPES = [
    ('pdf', 'PDF'),
    ('audio', 'Audio'),
    ('video', 'Video'),
    ('qcm', 'QCM'),
    ('form', 'Form'),
    ('consigne', 'Consigne'),
]


class Asset(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='assets')
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
        unique_together = [['step', 'order_index']]
        indexes = [
            models.Index(fields=['step']),
            models.Index(fields=['type']),
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
    options = models.JSONField()  # Array of strings
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
