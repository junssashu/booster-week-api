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
        """
        # Payment checks
        if self.payment_status == 'pending':
            return False, 'payment'

        if self.payment_status != 'completed' and self.payment_type != 'full':
            # Installment with partial payment: only first half of degrees
            total_degrees = self.program.degrees.count()
            cutoff = math.ceil(total_degrees / 2)
            if degree.order_index >= cutoff:
                return False, 'payment'

        # Completion check: all steps of all previous degrees must average >= 70%
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
                if avg < 70:
                    return False, 'completion'

        return True, None

    @property
    def installment_amount(self):
        if self.payment_type == 'installment':
            return math.ceil(self.total_amount / 2)
        return None

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['enrollment']),
            models.Index(fields=['transaction_ref']),
            models.Index(fields=['mf_transaction_id']),
            models.Index(fields=['status']),
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
