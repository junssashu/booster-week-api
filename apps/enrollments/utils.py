from datetime import timedelta

from django.conf import settings
from django.utils import timezone


def _get_expiry_minutes():
    """Read payment expiry from AppSettings DB, fallback to env/settings."""
    try:
        from apps.content.models import AppSettings
        app_settings = AppSettings.objects.filter(id=1).first()
        if app_settings and app_settings.payment_expiry_minutes:
            return app_settings.payment_expiry_minutes
    except Exception:
        pass
    return getattr(settings, 'PAYMENT_EXPIRY_MINUTES', 15)


def check_and_expire_payment(payment):
    """If payment is pending and past expiry window, mark it expired."""
    if payment and payment.status == 'pending':
        expiry_minutes = _get_expiry_minutes()
        expiry = payment.created_at + timedelta(minutes=expiry_minutes)
        if timezone.now() > expiry:
            payment.status = 'expired'
            payment.save(update_fields=['status', 'updated_at'])
    return payment
