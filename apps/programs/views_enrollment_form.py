"""
Lightweight views for the enrollment form flow.

These endpoints serve form fields and accept form submissions for programs that
have an enrollment_form_asset_id set. Unlike the regular asset/progress views,
they do NOT require the user to be already enrolled — the form appears BEFORE
enrollment/payment.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import NotFoundError, ValidationError
from apps.core.utils import generate_prefixed_id
from .models import Program, Asset, FormFieldDef


class ProgramEnrollmentFormView(APIView):
    """
    GET /programs/{program_id}/enrollment-form
    Return the form fields for a program's enrollment form asset.
    Requires authentication but NOT enrollment (user hasn't enrolled yet).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, program_id):
        try:
            program = Program.objects.get(id=program_id)
        except Program.DoesNotExist:
            raise NotFoundError('Programme introuvable.')

        if not program.enrollment_form_asset_id:
            return Response({'data': {'formFields': []}})

        try:
            asset = Asset.objects.prefetch_related('form_fields').get(
                id=program.enrollment_form_asset_id,
                type='form',
            )
        except Asset.DoesNotExist:
            return Response({'data': {'formFields': []}})

        fields = [
            {
                'id': f.id,
                'label': f.label,
                'type': f.type,
                'required': f.required,
                'selectOptions': f.select_options,
            }
            for f in asset.form_fields.order_by('order_index')
        ]

        return Response({'data': {
            'assetId': asset.id,
            'formFields': fields,
        }})


class ProgramEnrollmentFormSubmitView(APIView):
    """
    POST /programs/{program_id}/enrollment-form/submit
    Submit enrollment form responses.
    Requires authentication but NOT enrollment — user submits form before paying.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, program_id):
        import re
        from django.utils import timezone

        try:
            program = Program.objects.get(id=program_id)
        except Program.DoesNotExist:
            raise NotFoundError('Programme introuvable.')

        if not program.enrollment_form_asset_id:
            raise NotFoundError('Ce programme n\'a pas de formulaire d\'inscription.')

        try:
            asset = Asset.objects.prefetch_related('form_fields').get(
                id=program.enrollment_form_asset_id,
                type='form',
            )
        except Asset.DoesNotExist:
            raise NotFoundError('Formulaire introuvable.')

        responses = request.data.get('responses', [])
        if not isinstance(responses, list):
            raise ValidationError('responses doit etre une liste de {fieldId, value}.')

        field_defs = {f.id: f for f in asset.form_fields.all()}
        response_map = {
            r.get('fieldId', ''): r.get('value', '')
            for r in responses
            if isinstance(r, dict)
        }

        errors = []
        for field_id, field_def in field_defs.items():
            value = response_map.get(field_id, '')
            if field_def.required and not value:
                errors.append({'field': field_id, 'message': f'{field_def.label} est requis.'})
            if value and field_def.type == 'email':
                if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                    errors.append({'field': field_id, 'message': 'Format email invalide.'})
            if value and field_def.type == 'select' and field_def.select_options:
                if value not in field_def.select_options:
                    errors.append({'field': field_id, 'message': f'Valeur invalide.'})

        if errors:
            raise ValidationError('Validation du formulaire echouee.', errors)

        from apps.progress.models import FormSubmission
        submission_id = generate_prefixed_id('sub')
        FormSubmission.objects.create(
            id=submission_id,
            user=request.user,
            asset=asset,
            responses=responses,
        )

        return Response({'data': {
            'assetId': asset.id,
            'submissionId': submission_id,
            'submittedAt': timezone.now().isoformat(),
            'message': 'Formulaire soumis avec succes.',
        }}, status=201)
