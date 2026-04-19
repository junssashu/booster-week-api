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
    num_installments = models.IntegerField(default=2)
    whatsapp_community_url = models.TextField(null=True, blank=True)
    promotion_details = models.TextField(null=True, blank=True)
    modules_text = models.TextField(null=True, blank=True)
    degrees_per_installment = models.JSONField(null=True, blank=True)
    completion_threshold = models.IntegerField(default=70)
    preview_assets = models.JSONField(null=True, blank=True)
    enrollment_form_asset_id = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='Asset ID of the form shown before payment during enrollment.',
    )
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


DEGREE_FILE_TYPES = [
    ('pdf', 'PDF'), ('audio', 'Audio'), ('video', 'Video'), ('image', 'Image'),
]


class DegreeFile(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE, related_name='files')
    type = models.CharField(max_length=20, choices=DEGREE_FILE_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    external_url = models.TextField(null=True, blank=True)
    order_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'degree_files'
        ordering = ['order_index']
        unique_together = [['degree', 'order_index']]
        indexes = [models.Index(fields=['degree'])]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('dfile')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.type}: {self.title}'


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
