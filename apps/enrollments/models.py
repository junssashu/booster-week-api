import math
import random
import string
import uuid

from django.db import models
from django.utils import timezone

from apps.accounts.models import User
from apps.core.utils import generate_prefixed_id
from apps.programs.models import Program


class Enrollment(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='enrollments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    payment_type = models.CharField(max_length=20)  # full, installment
    payment_status = models.CharField(max_length=20, default='pending')  # pending, partial, completed
    amount_paid = models.IntegerField(default=0)
    total_amount = models.IntegerField()
    enrollment_date = models.DateTimeField(auto_now_add=True)
    installment_config_snapshot = models.JSONField(default=dict, blank=True)
    mandataire = models.ForeignKey(
        'accounts.User',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mandated_enrollments',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'enrollments'
        unique_together = [['program', 'user']]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['payment_status']),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('enr')
        super().save(*args, **kwargs)

    def can_access_degree(self, degree):
        """Check if a degree is accessible based on payment and completion rules.

        Returns True if accessible, False otherwise.
        Use can_access_degree_detail() for the detailed lock_reason.
        """
        _, lock_reason = self.can_access_degree_detail(degree)
        return lock_reason is None

    def can_access_degree_detail(self, degree):
        """Check if a degree is accessible and return (accessible, lock_reason).

        lock_reason is one of: 'payment', 'completion', or None (accessible).
        Uses installment_config_snapshot if available to prevent admin config
        changes from breaking existing enrollments.
        """
        # Payment checks
        if self.payment_status == 'pending':
            return False, 'payment'

        if self.payment_status != 'completed' and self.payment_type != 'full':
            # Installment with partial payment: determine which degrees are unlocked
            snapshot = self.installment_config_snapshot or {}
            total_degrees = self.program.degrees.count()
            dpi = snapshot.get('degrees_per_installment') or self.program.degrees_per_installment  # e.g. [2, 1]
            num_inst = snapshot.get('num_installments') or self.program.num_installments or 2

            if dpi and isinstance(dpi, list) and len(dpi) > 0:
                # Custom mapping: sum of first installment(s) paid determines cutoff
                # For partial payment, only 1st installment is paid
                cutoff = dpi[0] if len(dpi) > 0 else math.ceil(total_degrees / 2)
            else:
                # Default: split evenly across installments
                cutoff = math.ceil(total_degrees / num_inst)

            if degree.order_index >= cutoff:
                return False, 'payment'

        # Completion check: configurable threshold (default 70%)
        snapshot = self.installment_config_snapshot or {}
        threshold = snapshot.get('completion_threshold') or self.program.completion_threshold or 70
        if degree.order_index > 0:
            from apps.programs.models import Degree as DegreeModel
            from apps.progress.models import StepProgress
            previous_degrees = DegreeModel.objects.filter(
                program=self.program,
                order_index__lt=degree.order_index,
            ).prefetch_related('steps')

            for prev_degree in previous_degrees:
                steps = prev_degree.steps.all()
                total_steps = steps.count()
                if total_steps == 0:
                    continue
                progress_records = dict(
                    StepProgress.objects.filter(
                        user=self.user, step__in=steps
                    ).values_list('step_id', 'completion_percentage')
                )
                total_pct = sum(progress_records.get(step.id, 0) for step in steps)
                avg = total_pct / total_steps
                if avg < threshold:
                    return False, 'completion'

        return True, None

    @property
    def installment_amount(self):
        if self.payment_type == 'installment':
            num_inst = self.program.num_installments or 2
            return math.ceil(self.total_amount / num_inst)
        return None

    def all_degrees_completed(self):
        """Check if all degrees have >= threshold avg step completion."""
        from apps.progress.models import StepProgress
        threshold = self.program.completion_threshold or 70
        for degree in self.program.degrees.all():
            steps = list(degree.steps.all())
            if not steps:
                continue
            total = 0
            for s in steps:
                sp = StepProgress.objects.filter(user=self.user, step=s).first()
                total += (sp.completion_percentage if sp else 0)
            if total / len(steps) < threshold:
                return False
        return True

    def get_next_unlocked(self):
        """Return (next_degree, next_step) the user should work on."""
        from apps.progress.models import StepProgress
        for degree in self.program.degrees.order_by('order_index'):
            can_access, _ = self.can_access_degree_detail(degree)
            if not can_access:
                return (None, None)
            for step in degree.steps.order_by('order_index'):
                sp = StepProgress.objects.filter(user=self.user, step=step).first()
                if not sp or sp.completion_percentage < 70:
                    return (degree, step)
        return (None, None)

    def __str__(self):
        return f'{self.user} → {self.program} ({self.payment_status})'


class Payment(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments')
    amount = models.IntegerField()
    method = models.CharField(max_length=20)  # orangeMoney, mtnMoney, wave
    status = models.CharField(max_length=20, default='pending')  # pending, completed, failed, expired
    date = models.DateTimeField(auto_now_add=True)
    transaction_ref = models.CharField(max_length=255, null=True, blank=True)
    mf_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    payment_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['enrollment']),
            models.Index(fields=['transaction_ref']),
            models.Index(fields=['mf_transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('pay')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Pay {self.id}: {self.amount} XOF ({self.status})'


class PromoCode(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    code = models.CharField(max_length=10, unique=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promo_codes')
    discount_percent = models.IntegerField(default=20)  # 1-100
    max_uses = models.IntegerField(default=1)
    current_uses = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'promo_codes'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('promo')
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_code():
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=8))
            if not PromoCode.objects.filter(code=code).exists():
                return code

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.current_uses >= self.max_uses:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def __str__(self):
        return f'Promo {self.code} ({self.discount_percent}%)'


class PromoCodeRedemption(models.Model):
    id = models.CharField(max_length=50, primary_key=True, default=None, editable=False)
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    discount_applied = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'promo_code_redemptions'
        unique_together = [['promo_code', 'user']]

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_prefixed_id('redemp')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} redeemed {self.promo_code.code}'
