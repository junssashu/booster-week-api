import uuid

from django.db import models

from apps.accounts.models import User
from apps.programs.models import Asset, Program, Step


class AssetCompletion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asset_completions')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='completions')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='asset_completions')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'asset_completions'
        unique_together = [['user', 'asset']]
        indexes = [models.Index(fields=['user', 'program'])]


class QCMAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qcm_attempts')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='qcm_attempts')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    passed = models.BooleanField()
    answers = models.JSONField()
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'qcm_attempts'
        indexes = [
            models.Index(fields=['user', 'asset']),
        ]


class ConsigneAcceptance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consigne_acceptances')
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='consigne_acceptances')
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'consigne_acceptances'
        unique_together = [['user', 'step']]


class FormSubmission(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='form_submissions')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='form_submissions')
    responses = models.JSONField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'form_submissions'
        indexes = [
            models.Index(fields=['user', 'asset']),
            models.Index(fields=['asset']),
        ]


class StepProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='step_progress')
    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name='progress_records')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='step_progress')
    status = models.CharField(max_length=20, default='locked')  # locked, available, completed
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'step_progress'
        unique_together = [['user', 'step']]
        indexes = [models.Index(fields=['user', 'program'])]
