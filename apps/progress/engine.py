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
        if asset.type in ('pdf', 'audio', 'video', 'image'):
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

    # Always update completion percentage incrementally
    _, _, current_progress = get_step_progress_info(user, step)
    pct = round(current_progress * 100)

    sp, _ = StepProgress.objects.get_or_create(
        user=user,
        step=step,
        defaults={'program': step.degree.program, 'status': 'in_progress', 'completion_percentage': pct}
    )

    # Update percentage if changed
    if sp.completion_percentage != pct:
        sp.completion_percentage = pct
        sp.save(update_fields=['completion_percentage', 'updated_at'])

    if not all_complete:
        # Update status to in_progress if not already
        if sp.status not in ('in_progress', 'completed'):
            sp.status = 'in_progress'
            sp.save(update_fields=['status', 'updated_at'])
        # Check if >= 70% unlocks next step
        if pct >= 70:
            unlock_next_step(user, step)
        return False, None

    # Mark step as completed
    if sp.status != 'completed':
        sp.status = 'completed'
        sp.completion_percentage = 100
        sp.save(update_fields=['status', 'completion_percentage', 'updated_at'])

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
        order_index__gt=completed_step.order_index,
    ).order_by('order_index').first()

    if not next_step:
        # Try first step of next degree
        next_degree = Degree.objects.filter(
            program=program,
            order_index__gt=degree.order_index,
        ).order_by('order_index').first()

        if next_degree:
            # Check if next degree is accessible
            enrollment = Enrollment.objects.filter(
                user=user, program=program
            ).first()
            if enrollment and enrollment.can_access_degree(next_degree):
                next_step = Step.objects.filter(
                    degree=next_degree,
                ).order_by('order_index').first()

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
        if asset.type in ('pdf', 'audio', 'video', 'image'):
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
