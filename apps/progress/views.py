import re

from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ForbiddenError, NotFoundError, PaymentRequiredError, ValidationError
from apps.core.throttles import QCMThrottle
from apps.core.utils import generate_prefixed_id
from django.shortcuts import get_object_or_404
from apps.enrollments.models import Enrollment
from apps.programs.models import Asset, Step, PriseDeContact

from .engine import check_step_completion, get_step_progress_info
from .models import AssetCompletion, ConsigneAcceptance, FormSubmission, PriseDeContactAcceptance, QCMAttempt, StepProgress


def _require_enrollment_and_access(user, asset_or_step):
    """Validate enrollment and access for an asset or step."""
    if isinstance(asset_or_step, Asset):
        step = asset_or_step.step
    else:
        step = asset_or_step

    degree = step.degree
    program = degree.program

    enrollment = Enrollment.objects.filter(user=user, program=program).first()
    if not enrollment or enrollment.payment_status == 'pending':
        raise PaymentRequiredError('You must be enrolled and have paid.')

    accessible, lock_reason = enrollment.can_access_degree_detail(degree)
    if not accessible:
        if lock_reason == 'completion':
            raise ForbiddenError('Complete previous degrees with at least 70% average to unlock this degree.')
        raise ForbiddenError('Complete second payment to unlock this degree.')

    sp = StepProgress.objects.filter(user=user, step=step).first()
    if sp and sp.status == 'locked':
        raise ForbiddenError('Complete previous step first.')

    if not sp:
        # No progress record: first step in degree is always accessible
        prev_step = step.degree.steps.filter(order_index__lt=step.order_index).order_by('-order_index').first()
        if prev_step:
            prev_sp = StepProgress.objects.filter(user=user, step=prev_step).first()
            if not prev_sp or prev_sp.completion_percentage < 70:
                raise ForbiddenError('Complete previous step first.')

    return enrollment, step


class ProgressView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Progress'],
        operation_id='progress_get',
        summary='Get user progress across all programs',
        description=(
            'Returns the authenticated user\'s full progress across all enrolled programs, '
            'including per-degree and per-step breakdowns. Optionally filter by a single program.'
        ),
        parameters=[
            inline_serializer(
                name='ProgressQueryParams',
                fields={
                    'programId': drf_serializers.CharField(
                        required=False,
                        help_text='Filter progress to a specific program ID.',
                    ),
                },
            ),
        ],
        responses={
            200: inline_serializer(
                name='ProgressResponse',
                fields={
                    'data': inline_serializer(
                        name='ProgressData',
                        fields={
                            'overallProgress': drf_serializers.FloatField(help_text='Overall progress across all programs (0-1).'),
                            'programs': drf_serializers.ListField(
                                child=inline_serializer(
                                    name='ProgramProgress',
                                    fields={
                                        'programId': drf_serializers.CharField(),
                                        'programName': drf_serializers.CharField(),
                                        'progress': drf_serializers.FloatField(help_text='Program progress (0-1).'),
                                        'completedSteps': drf_serializers.IntegerField(),
                                        'totalSteps': drf_serializers.IntegerField(),
                                        'isCompleted': drf_serializers.BooleanField(),
                                        'degrees': drf_serializers.ListField(
                                            child=inline_serializer(
                                                name='DegreeProgress',
                                                fields={
                                                    'degreeId': drf_serializers.CharField(),
                                                    'title': drf_serializers.CharField(),
                                                    'progress': drf_serializers.FloatField(help_text='Degree progress (0-1).'),
                                                    'completedSteps': drf_serializers.IntegerField(),
                                                    'totalSteps': drf_serializers.IntegerField(),
                                                    'steps': drf_serializers.ListField(
                                                        child=inline_serializer(
                                                            name='StepProgress',
                                                            fields={
                                                                'stepId': drf_serializers.CharField(),
                                                                'title': drf_serializers.CharField(),
                                                                'status': drf_serializers.ChoiceField(choices=['locked', 'in_progress', 'completed']),
                                                                'progress': drf_serializers.FloatField(help_text='Step progress (0-1).'),
                                                                'completedAssets': drf_serializers.IntegerField(),
                                                                'totalAssets': drf_serializers.IntegerField(),
                                                                'qcmScore': drf_serializers.FloatField(allow_null=True, help_text='Best QCM score or null.'),
                                                                'consigneAccepted': drf_serializers.BooleanField(),
                                                            },
                                                        ),
                                                    ),
                                                },
                                            ),
                                        ),
                                    },
                                ),
                            ),
                        },
                    ),
                },
            ),
        },
    )
    def get(self, request):
        user = request.user
        program_id_filter = request.query_params.get('programId')

        enrollments = Enrollment.objects.filter(user=user).exclude(
            payment_status='pending'
        ).select_related('program')

        if program_id_filter:
            enrollments = enrollments.filter(program_id=program_id_filter)

        programs_data = []
        total_progress = 0.0

        for enrollment in enrollments:
            program = enrollment.program
            degrees = program.degrees.all().order_by('order_index')

            degrees_data = []
            program_completed_steps = 0
            program_total_steps = 0

            for degree in degrees:
                steps = degree.steps.all().order_by('order_index')
                steps_data = []
                degree_completed = 0
                degree_total = steps.count()
                program_total_steps += degree_total

                for step in steps:
                    sp = StepProgress.objects.filter(user=user, step=step).first()
                    step_status = sp.status if sp else 'locked'
                    completed_assets, total_assets, step_prog = get_step_progress_info(user, step)

                    if step_status == 'completed':
                        degree_completed += 1
                        program_completed_steps += 1

                    # Get best QCM score for this step
                    qcm_assets = step.assets.filter(type='qcm')
                    qcm_score = None
                    if qcm_assets.exists():
                        best = QCMAttempt.objects.filter(
                            user=user, asset__in=qcm_assets
                        ).order_by('-score').first()
                        if best:
                            qcm_score = float(best.score)

                    consigne_accepted = ConsigneAcceptance.objects.filter(
                        user=user, step=step
                    ).exists()

                    steps_data.append({
                        'stepId': step.id,
                        'title': step.title,
                        'status': step_status,
                        'progress': round(step_prog, 2),
                        'completedAssets': completed_assets,
                        'totalAssets': total_assets,
                        'qcmScore': qcm_score,
                        'consigneAccepted': consigne_accepted,
                    })

                degree_progress = degree_completed / degree_total if degree_total > 0 else 0.0
                degrees_data.append({
                    'degreeId': degree.id,
                    'title': degree.title,
                    'progress': round(degree_progress, 2),
                    'completedSteps': degree_completed,
                    'totalSteps': degree_total,
                    'steps': steps_data,
                })

            program_progress = program_completed_steps / program_total_steps if program_total_steps > 0 else 0.0
            total_progress += program_progress

            programs_data.append({
                'programId': program.id,
                'programName': program.name,
                'progress': round(program_progress, 2),
                'completedSteps': program_completed_steps,
                'totalSteps': program_total_steps,
                'isCompleted': program_completed_steps == program_total_steps and program_total_steps > 0,
                'degrees': degrees_data,
            })

        overall = total_progress / len(programs_data) if programs_data else 0.0

        return Response({
            'data': {
                'overallProgress': round(overall, 2),
                'programs': programs_data,
            }
        })


class MarkAssetCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Progress'],
        operation_id='progress_mark_asset_complete',
        summary='Mark a media asset as completed',
        description=(
            'Marks a pdf, audio, or video asset as completed for the authenticated user. '
            'Idempotent: calling again on an already-completed asset has no adverse effect. '
            'The consigne for the step must be accepted first if one exists.'
        ),
        request=None,
        responses={
            200: inline_serializer(
                name='MarkAssetCompleteResponse',
                fields={
                    'data': inline_serializer(
                        name='MarkAssetCompleteData',
                        fields={
                            'assetId': drf_serializers.CharField(),
                            'programId': drf_serializers.CharField(),
                            'stepId': drf_serializers.CharField(),
                            'isCompleted': drf_serializers.BooleanField(),
                            'stepProgress': drf_serializers.FloatField(help_text='Step progress after completion (0-1).'),
                            'stepCompleted': drf_serializers.BooleanField(help_text='Whether the entire step is now completed.'),
                            'nextStepUnlocked': drf_serializers.DictField(
                                required=False,
                                help_text='Info about the next step if it was unlocked. Present only when a new step is unlocked.',
                            ),
                        },
                    ),
                },
            ),
        },
    )
    def post(self, request, asset_id):
        try:
            asset = Asset.objects.select_related('step__degree__program').get(id=asset_id)
        except Asset.DoesNotExist:
            raise NotFoundError('Asset does not exist.')

        if asset.type not in ('pdf', 'audio', 'video', 'image'):
            raise ValidationError('Only pdf, audio, video, and image assets can be marked complete this way.')

        enrollment, step = _require_enrollment_and_access(request.user, asset)

        # Check consigne gate
        has_consigne = step.assets.filter(type='consigne').exists()
        if has_consigne:
            if not ConsigneAcceptance.objects.filter(user=request.user, step=step).exists():
                raise ForbiddenError('Accept the consigne before completing assets.')

        # Mark complete (idempotent)
        AssetCompletion.objects.get_or_create(
            user=request.user,
            asset=asset,
            defaults={'program': step.degree.program}
        )

        # Check step completion
        step_completed, next_step_info = check_step_completion(request.user, step)
        _, _, step_progress = get_step_progress_info(request.user, step)

        data = {
            'assetId': asset.id,
            'programId': step.degree.program_id,
            'stepId': step.id,
            'isCompleted': True,
            'stepProgress': round(step_progress, 2),
            'stepCompleted': step_completed,
        }

        if next_step_info:
            data['nextStepUnlocked'] = next_step_info

        return Response({'data': data})


class QCMSubmitView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [QCMThrottle]

    @extend_schema(
        tags=['Progress'],
        operation_id='progress_qcm_submit',
        summary='Submit QCM answers and get graded results',
        description=(
            'Submits answers for a QCM (multiple-choice quiz) asset and returns graded results. '
            'The number of answers must match the number of questions. '
            'If the user passes, the asset is marked as completed automatically.'
        ),
        request=inline_serializer(
            name='QCMSubmitRequest',
            fields={
                'answers': drf_serializers.ListField(
                    child=inline_serializer(
                        name='QCMAnswer',
                        fields={
                            'questionIndex': drf_serializers.IntegerField(help_text='Zero-based index of the question.'),
                            'selectedOptionIndex': drf_serializers.IntegerField(help_text='Zero-based index of the selected option.'),
                        },
                    ),
                    help_text='List of answers, one per question.',
                ),
            },
        ),
        responses={
            200: inline_serializer(
                name='QCMSubmitResponse',
                fields={
                    'data': inline_serializer(
                        name='QCMSubmitData',
                        fields={
                            'assetId': drf_serializers.CharField(),
                            'score': drf_serializers.FloatField(help_text='Score as a percentage (0-100).'),
                            'passingScore': drf_serializers.FloatField(help_text='Minimum passing score percentage.'),
                            'passed': drf_serializers.BooleanField(),
                            'totalQuestions': drf_serializers.IntegerField(),
                            'correctAnswers': drf_serializers.IntegerField(),
                            'results': drf_serializers.ListField(
                                child=inline_serializer(
                                    name='QCMQuestionResult',
                                    fields={
                                        'questionIndex': drf_serializers.IntegerField(),
                                        'correct': drf_serializers.BooleanField(),
                                        'correctOptionIndex': drf_serializers.IntegerField(),
                                    },
                                ),
                            ),
                        },
                    ),
                },
            ),
        },
    )
    def post(self, request, asset_id):
        try:
            asset = Asset.objects.select_related('step__degree__program').prefetch_related('questions').get(id=asset_id)
        except Asset.DoesNotExist:
            raise NotFoundError('Asset does not exist.')

        if asset.type != 'qcm':
            raise NotFoundError('Asset is not a QCM type.')

        enrollment, step = _require_enrollment_and_access(request.user, asset)

        # Check consigne gate
        has_consigne = step.assets.filter(type='consigne').exists()
        if has_consigne:
            if not ConsigneAcceptance.objects.filter(user=request.user, step=step).exists():
                raise ForbiddenError('Accept the consigne before submitting QCM.')

        answers = request.data.get('answers', [])
        questions = list(asset.questions.all().order_by('order_index'))

        if len(answers) != len(questions):
            raise ValidationError(
                f'Expected {len(questions)} answers, got {len(answers)}.',
                [{'field': 'answers', 'message': f'Expected {len(questions)} answers'}]
            )

        # Grade
        correct_count = 0
        results = []
        for answer in answers:
            q_idx = answer.get('questionIndex')
            selected = answer.get('selectedOptionIndex')

            if q_idx is None or selected is None:
                raise ValidationError('Each answer must have questionIndex and selectedOptionIndex.')

            if q_idx < 0 or q_idx >= len(questions):
                raise ValidationError(f'Invalid questionIndex: {q_idx}')

            question = questions[q_idx]
            is_correct = selected == question.correct_index
            if is_correct:
                correct_count += 1

            results.append({
                'questionIndex': q_idx,
                'correct': is_correct,
                'correctOptionIndex': question.correct_index,
            })

        score = (correct_count / len(questions)) * 100 if questions else 0
        passed = score >= asset.passing_score

        # Record attempt
        QCMAttempt.objects.create(
            user=request.user,
            asset=asset,
            score=score,
            passed=passed,
            answers=answers,
        )

        # Update step completion_percentage with QCM score (use best score)
        sp = StepProgress.objects.filter(user=request.user, step=step).first()
        if sp:
            rounded_score = round(score)
            if rounded_score > sp.completion_percentage:
                sp.completion_percentage = rounded_score
                sp.save(update_fields=['completion_percentage', 'updated_at'])

        # If passed, mark as completed
        if passed:
            AssetCompletion.objects.get_or_create(
                user=request.user,
                asset=asset,
                defaults={'program': step.degree.program}
            )
            check_step_completion(request.user, step)

        return Response({
            'data': {
                'assetId': asset.id,
                'score': round(score, 1),
                'passingScore': asset.passing_score,
                'passed': passed,
                'totalQuestions': len(questions),
                'correctAnswers': correct_count,
                'results': results,
            }
        })


class FormSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Progress'],
        operation_id='progress_form_submit',
        summary='Submit form responses',
        description=(
            'Submits responses for a form-type asset. '
            'Validates required fields, email format, and select options. '
            'On success the asset is marked as completed.'
        ),
        request=inline_serializer(
            name='FormSubmitRequest',
            fields={
                'responses': drf_serializers.ListField(
                    child=inline_serializer(
                        name='FormFieldResponse',
                        fields={
                            'fieldId': drf_serializers.CharField(help_text='ID of the form field.'),
                            'value': drf_serializers.CharField(help_text='User-provided value for the field.'),
                        },
                    ),
                    help_text='List of field responses.',
                ),
            },
        ),
        responses={
            201: inline_serializer(
                name='FormSubmitResponse',
                fields={
                    'data': inline_serializer(
                        name='FormSubmitData',
                        fields={
                            'assetId': drf_serializers.CharField(),
                            'submissionId': drf_serializers.CharField(),
                            'submittedAt': drf_serializers.DateTimeField(),
                            'message': drf_serializers.CharField(),
                        },
                    ),
                },
            ),
        },
    )
    def post(self, request, asset_id):
        try:
            asset = Asset.objects.select_related('step__degree__program').prefetch_related('form_fields').get(id=asset_id)
        except Asset.DoesNotExist:
            raise NotFoundError('Asset does not exist.')

        if asset.type != 'form':
            raise NotFoundError('Asset is not a form type.')

        enrollment, step = _require_enrollment_and_access(request.user, asset)

        # Check consigne gate
        has_consigne = step.assets.filter(type='consigne').exists()
        if has_consigne:
            if not ConsigneAcceptance.objects.filter(user=request.user, step=step).exists():
                raise ForbiddenError('Accept the consigne before submitting form.')

        responses = request.data.get('responses', [])
        field_defs = {f.id: f for f in asset.form_fields.all()}

        # Validate responses format
        if not isinstance(responses, list):
            raise ValidationError('Responses must be a list of {fieldId, value} objects.')

        errors = []
        response_map = {}
        for r in responses:
            if isinstance(r, dict):
                response_map[r.get('fieldId', '')] = r.get('value', '')
            elif isinstance(r, str):
                # Legacy format — skip invalid entries
                continue

        for field_id, field_def in field_defs.items():
            value = response_map.get(field_id, '')
            if field_def.required and not value:
                errors.append({'field': field_id, 'message': f'{field_def.label} is required.'})
            if value and field_def.type == 'email':
                if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                    errors.append({'field': field_id, 'message': 'Invalid email format.'})
            if value and field_def.type == 'select' and field_def.select_options:
                if value not in field_def.select_options:
                    errors.append({'field': field_id, 'message': f'Invalid selection. Choose from: {field_def.select_options}'})

        if errors:
            raise ValidationError('Form validation failed.', errors)

        submission_id = generate_prefixed_id('sub')
        FormSubmission.objects.create(
            id=submission_id,
            user=request.user,
            asset=asset,
            responses=responses,
        )

        # Mark as completed
        AssetCompletion.objects.get_or_create(
            user=request.user,
            asset=asset,
            defaults={'program': step.degree.program}
        )
        check_step_completion(request.user, step)

        return Response({
            'data': {
                'assetId': asset.id,
                'submissionId': submission_id,
                'submittedAt': timezone.now().isoformat(),
                'message': 'Formulaire soumis avec succes.',
            }
        }, status=status.HTTP_201_CREATED)


class ConsigneAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Progress'],
        operation_id='progress_consigne_accept',
        summary='Accept step consigne',
        description=(
            'Accepts the consigne (instructions/agreement) for a step. '
            'Idempotent: calling again returns the same acceptance timestamp. '
            'The step must have a consigne asset and the user must be enrolled.'
        ),
        request=None,
        responses={
            200: inline_serializer(
                name='ConsigneAcceptResponse',
                fields={
                    'data': inline_serializer(
                        name='ConsigneAcceptData',
                        fields={
                            'stepId': drf_serializers.CharField(),
                            'consigneAccepted': drf_serializers.BooleanField(),
                            'acceptedAt': drf_serializers.DateTimeField(),
                        },
                    ),
                },
            ),
        },
    )
    def post(self, request, step_id):
        try:
            step = Step.objects.select_related('degree__program').get(id=step_id)
        except Step.DoesNotExist:
            raise NotFoundError('Step does not exist.')

        # Check consigne exists
        if not step.assets.filter(type='consigne').exists():
            raise NotFoundError('Step has no consigne.')

        enrollment, _ = _require_enrollment_and_access(request.user, step)

        # Idempotent acceptance
        acceptance, created = ConsigneAcceptance.objects.get_or_create(
            user=request.user,
            step=step,
        )

        return Response({
            'data': {
                'stepId': step.id,
                'consigneAccepted': True,
                'acceptedAt': acceptance.accepted_at.isoformat(),
            }
        })


class PriseDeContactAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pdc_id):
        pdc = get_object_or_404(PriseDeContact, id=pdc_id)
        acceptance, created = PriseDeContactAcceptance.objects.get_or_create(
            user=request.user,
            prise_de_contact=pdc,
        )
        return Response({
            'accepted': True,
            'acceptedAt': acceptance.accepted_at.isoformat(),
        })
