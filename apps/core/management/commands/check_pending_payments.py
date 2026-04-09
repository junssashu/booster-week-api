"""
Background job to check and complete pending payments via MoneyFusion API.

Polls all payments with status='pending' older than 2 minutes.
If MoneyFusion says 'paid', completes the payment atomically.
If MoneyFusion says 'failed'/'no paid', marks as failed.
If still 'pending' and older than PAYMENT_EXPIRY_MINUTES, marks as expired.

Usage:
  python manage.py check_pending_payments          # Run once
  python manage.py check_pending_payments --loop    # Run continuously (every 60s)

Cron (recommended):
  */2 * * * * cd /app && python manage.py check_pending_payments >> /var/log/payment_checker.log 2>&1
"""
import logging
import time
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check pending payments with MoneyFusion and complete/fail them.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop',
            action='store_true',
            help='Run continuously in a loop (every 60 seconds)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Loop interval in seconds (default: 60)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Max payments to check per run (default: 50)',
        )

    def handle(self, *args, **options):
        self._batch_size = options['batch_size']
        if options['loop']:
            self.stdout.write('Starting payment checker loop...')
            while True:
                self._check_payments()
                time.sleep(options['interval'])
        else:
            self._check_payments()

    def _check_payments(self):
        from apps.enrollments.models import Payment
        from apps.enrollments.services import MoneyFusionService, MoneyFusionError
        from apps.enrollments.views import _complete_payment

        expiry_minutes = getattr(settings, 'PAYMENT_EXPIRY_MINUTES', 15)
        min_age = timezone.now() - timedelta(minutes=2)  # Only check payments older than 2 min
        expiry_cutoff = timezone.now() - timedelta(minutes=expiry_minutes)

        pending = Payment.objects.filter(
            status='pending',
            created_at__lt=min_age,
        ).select_related('enrollment', 'enrollment__user')[:self._batch_size]

        if not pending:
            return

        self.stdout.write(f'Checking {len(pending)} pending payment(s) (batch={self._batch_size}).')

        for payment in pending:
            token = payment.mf_transaction_id
            if not token:
                # No MoneyFusion token — mark as expired if old enough
                if payment.created_at < expiry_cutoff:
                    payment.status = 'expired'
                    payment.save(update_fields=['status', 'updated_at'])
                    logger.info('Payment %s expired (no MF token).', payment.id)
                    self.stdout.write(f'  {payment.id}: expired (no token)')
                continue

            # Check with MoneyFusion
            try:
                result = MoneyFusionService.verify_payment(token)
                mf_status = result.get('data', {}).get('statut', '')

                if mf_status == 'paid':
                    _complete_payment(payment.id)
                    logger.info('Payment %s completed via background check.', payment.id)
                    self.stdout.write(self.style.SUCCESS(
                        f'  {payment.id}: COMPLETED (MF confirmed paid)'
                    ))

                elif mf_status in ('failed', 'failure', 'no paid'):
                    payment.status = 'failed'
                    payment.save(update_fields=['status', 'updated_at'])
                    logger.info('Payment %s failed (MF status: %s).', payment.id, mf_status)
                    self.stdout.write(self.style.WARNING(
                        f'  {payment.id}: FAILED (MF status: {mf_status})'
                    ))

                elif mf_status == 'pending':
                    # Still pending on MF side — expire if too old
                    if payment.created_at < expiry_cutoff:
                        payment.status = 'expired'
                        payment.save(update_fields=['status', 'updated_at'])
                        logger.info('Payment %s expired after %d min.', payment.id, expiry_minutes)
                        self.stdout.write(f'  {payment.id}: expired (still pending after {expiry_minutes}min)')
                    else:
                        self.stdout.write(f'  {payment.id}: still pending on MF ({mf_status})')

                else:
                    logger.warning('Payment %s: unknown MF status "%s"', payment.id, mf_status)
                    self.stdout.write(self.style.WARNING(f'  {payment.id}: unknown MF status "{mf_status}"'))

            except MoneyFusionError as e:
                logger.warning('MF error checking payment %s: %s', payment.id, e)
                self.stdout.write(self.style.ERROR(f'  {payment.id}: MF error: {e}'))

            except Exception as e:
                logger.exception('Unexpected error checking payment %s', payment.id)
                self.stdout.write(self.style.ERROR(f'  {payment.id}: error: {e}'))
