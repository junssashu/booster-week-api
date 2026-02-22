import math
import uuid

from django.db import models

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
        """Check if a degree is accessible based on payment rules."""
        if self.payment_status == 'pending':
            return False
        if self.payment_status == 'completed':
            return True
        if self.payment_type == 'full' and self.payment_status != 'pending':
            return True
        # partial payment: only first half of degrees
        total_degrees = self.program.degrees.count()
        cutoff = math.ceil(total_degrees / 2)
        return degree.order_index < cutoff

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
