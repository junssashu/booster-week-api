import logging

from django.db import models, transaction

logger = logging.getLogger(__name__)


def _cleanup_enrollment_progress(user, program):
    """Remove all progress data for a user+program when enrollment is cancelled/deleted.

    Cleans up: StepProgress, AssetCompletion, QCMAttempt, FormSubmission,
    and PdcAcceptance for all steps/assets in the program.
    """
    from apps.progress.models import StepProgress, AssetCompletion, QCMAttempt, FormSubmission
    from apps.programs.models import Step, Asset, PriseDeContact

    steps = Step.objects.filter(degree__program=program)
    assets = Asset.objects.filter(step__degree__program=program)
    pdcs = PriseDeContact.objects.filter(
        models.Q(program=program) | models.Q(degree__program=program) | models.Q(step__degree__program=program)
    )

    StepProgress.objects.filter(user=user, step__in=steps).delete()
    AssetCompletion.objects.filter(user=user, asset__in=assets).delete()
    QCMAttempt.objects.filter(user=user, asset__in=assets).delete()
    FormSubmission.objects.filter(user=user, asset__in=assets).delete()

    from apps.progress.models import PriseDeContactAcceptance
    PriseDeContactAcceptance.objects.filter(user=user, prise_de_contact__in=pdcs).delete()

    logger.info('Cleaned up progress data for user=%s, program=%s', user.id, program.id)


def _complete_payment(payment_id):
    """Atomically complete a payment and update its enrollment.

    Uses select_for_update() to prevent race conditions between
    webhook and verify endpoints processing the same payment.

    Returns the updated payment, or None if already completed (idempotent).
    """
    from .models import Enrollment, Payment

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(id=payment_id)

        if payment.status == 'completed':
            return None

        payment.status = 'completed'
        payment.save()

        enrollment = Enrollment.objects.select_for_update().get(id=payment.enrollment_id)
        enrollment.amount_paid += payment.amount
        if enrollment.amount_paid >= enrollment.total_amount:
            enrollment.payment_status = 'completed'
        elif enrollment.amount_paid > 0:
            enrollment.payment_status = 'partial'
        enrollment.save()

        try:
            _initialize_progress(enrollment)
        except Exception:
            logger.exception('Failed to init progress for enrollment %s (payment still completed)', enrollment.id)

        return payment


def _initialize_progress(enrollment):
    """Initialize step_progress for the program on first payment."""
    from apps.progress.models import StepProgress

    existing = StepProgress.objects.filter(
        user=enrollment.user,
        program=enrollment.program,
    ).exists()
    if existing:
        return

    degrees = enrollment.program.degrees.all().order_by('order_index')
    first_step_set = False

    for degree in degrees:
        if not enrollment.can_access_degree(degree):
            continue
        steps = degree.steps.all().order_by('order_index')
        for step_obj in steps:
            step_status = 'locked'
            if not first_step_set:
                step_status = 'available'
                first_step_set = True

            StepProgress.objects.get_or_create(
                user=enrollment.user,
                step=step_obj,
                defaults={
                    'program': enrollment.program,
                    'status': step_status,
                }
            )
