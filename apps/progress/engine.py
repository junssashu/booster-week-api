"""Progress tracking engine — handles step completion and unlocking logic."""

from apps.enrollments.models import Enrollment
from apps.programs.models import Asset, Degree, Step

from .models import AssetCompletion, ConsigneAcceptance, FormSubmission, QCMAttempt, StepProgress


def check_step_completion(user, step):
    """Check if all assets in a step are completed and handle auto-completion.

    Returns (step_completed, next_step_info).
    """
    assets = step.assets.all()
    all_complete = True

    for asset in assets:
        if asset.type in ('pdf', 'audio', 'video'):
            if not AssetCompletion.objects.filter(user=user, asset=asset).exists():
                all_complete = False
                break
        elif asset.type == 'qcm':
            # Need a passing attempt
            if not QCMAttempt.objects.filter(user=user, asset=asset, passed=True).exists():
                all_complete = False
                break
        elif asset.type == 'form':
            if not FormSubmission.objects.filter(user=user, asset=asset).exists():
                all_complete = False
                break
        elif asset.type == 'consigne':
            if not ConsigneAcceptance.objects.filter(user=user, step=step).exists():
                all_complete = False
                break

    if not all_complete:
        return False, None

    # Mark step as completed
    sp, _ = StepProgress.objects.get_or_create(
        user=user,
        step=step,
        defaults={'program': step.degree.program, 'status': 'completed'}
    )
    if sp.status != 'completed':
        sp.status = 'completed'
        sp.save()

    # For steps without QCM, set completion_percentage to 100 when completed.
    # Steps with QCM have their completion_percentage set by the QCM submit view.
    has_qcm = step.assets.filter(type='qcm').exists()
    if not has_qcm and sp.completion_percentage != 100:
        sp.completion_percentage = 100
        sp.save(update_fields=['completion_percentage', 'updated_at'])

    # Unlock next step
    next_step_info = unlock_next_step(user, step)
    return True, next_step_info


def unlock_next_step(user, completed_step):
    """Unlock the next step after completion. Handles cross-degree unlock."""
    degree = completed_step.degree
    program = degree.program

    # Try next step in same degree
    next_step = Step.objects.filter(
        degree=degree,
        order_index=completed_step.order_index + 1,
    ).first()

    if not next_step:
        # Try first step of next degree
        next_degree = Degree.objects.filter(
            program=program,
            order_index=degree.order_index + 1,
        ).first()

        if next_degree:
            # Check if next degree is accessible
            enrollment = Enrollment.objects.filter(
                user=user, program=program
            ).first()
            if enrollment and enrollment.can_access_degree(next_degree):
                next_step = Step.objects.filter(
                    degree=next_degree, order_index=0
                ).first()

    if next_step:
        sp, created = StepProgress.objects.get_or_create(
            user=user,
            step=next_step,
            defaults={'program': program, 'status': 'available'}
        )
        if not created and sp.status == 'locked':
            sp.status = 'available'
            sp.save()

        return {
            'stepId': next_step.id,
            'title': next_step.title,
        }

    return None


def get_step_progress_info(user, step):
    """Get progress info for a step."""
    assets = step.assets.all()
    total = assets.count()
    completed = 0

    for asset in assets:
        if asset.type in ('pdf', 'audio', 'video'):
            if AssetCompletion.objects.filter(user=user, asset=asset).exists():
                completed += 1
        elif asset.type == 'qcm':
            if QCMAttempt.objects.filter(user=user, asset=asset, passed=True).exists():
                completed += 1
        elif asset.type == 'form':
            if FormSubmission.objects.filter(user=user, asset=asset).exists():
                completed += 1
        elif asset.type == 'consigne':
            if ConsigneAcceptance.objects.filter(user=user, step=step).exists():
                completed += 1

    progress = completed / total if total > 0 else 0.0
    return completed, total, progress
