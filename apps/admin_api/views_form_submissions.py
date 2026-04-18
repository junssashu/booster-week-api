import csv

from django.db.models import Q
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminOrAssistant
from apps.programs.models import Program
from apps.progress.models import FormSubmission
from .serializers import AdminFormSubmissionRowSerializer, AdminFormSubmissionDetailSerializer


def _get_enrollment_asset_ids():
    return set(
        Program.objects.exclude(enrollment_form_asset_id__isnull=True)
        .exclude(enrollment_form_asset_id='')
        .values_list('enrollment_form_asset_id', flat=True)
    )


def _build_queryset(params):
    qs = FormSubmission.objects.select_related(
        'user',
        'asset__program',
        'asset__step__degree__program',
    ).prefetch_related('asset__form_fields').order_by('-submitted_at')

    program_id = params.get('programId')
    if program_id:
        qs = qs.filter(
            Q(asset__program_id=program_id) |
            Q(asset__step__degree__program_id=program_id)
        )

    search = params.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__phone__icontains=search)
        )

    filter_type = params.get('type', '')
    if filter_type in ('enrollment', 'in-course'):
        enrollment_ids = _get_enrollment_asset_ids()
        if filter_type == 'enrollment':
            qs = qs.filter(asset_id__in=enrollment_ids)
        else:
            qs = qs.exclude(asset_id__in=enrollment_ids)

    return qs


class AdminFormSubmissionListView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        qs = _build_queryset(request.query_params)
        enrollment_ids = _get_enrollment_asset_ids()

        try:
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(200, max(1, int(request.query_params.get('pageSize', 50))))
        except (ValueError, TypeError):
            page, page_size = 1, 50

        total = qs.count()
        start = (page - 1) * page_size
        submissions = qs[start:start + page_size]

        serializer = AdminFormSubmissionRowSerializer(
            submissions, many=True,
            context={'enrollment_asset_ids': enrollment_ids},
        )
        return Response({'data': {
            'results': serializer.data,
            'count': total,
            'page': page,
            'pageSize': page_size,
        }})


class AdminFormSubmissionDetailView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request, submission_id):
        try:
            submission = FormSubmission.objects.select_related(
                'user', 'asset',
            ).prefetch_related('asset__form_fields').get(id=submission_id)
        except FormSubmission.DoesNotExist:
            return Response({'error': 'Introuvable.'}, status=404)

        return Response({'data': AdminFormSubmissionDetailSerializer(submission).data})


class AdminFormSubmissionExportView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        qs = _build_queryset(request.query_params)
        enrollment_ids = _get_enrollment_asset_ids()

        submissions_data = []
        all_labels = []
        label_set = set()

        for sub in qs:
            field_map = {f.id: f.label for f in sub.asset.form_fields.all()}
            resolved = [
                {
                    'label': field_map.get(r.get('fieldId', ''), r.get('fieldId', '')),
                    'value': r.get('value', ''),
                }
                for r in (sub.responses or [])
                if isinstance(r, dict)
            ]
            submissions_data.append((sub, resolved))
            for item in resolved:
                if item['label'] not in label_set:
                    label_set.add(item['label'])
                    all_labels.append(item['label'])

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="formulaires.csv"'
        response.write('\ufeff')  # BOM for Excel UTF-8

        writer = csv.writer(response)
        writer.writerow(['Etudiant', 'Telephone', 'Programme', 'Formulaire', 'Type', 'Date'] + all_labels)

        for sub, resolved in submissions_data:
            resp_map = {item['label']: item['value'] for item in resolved}
            type_label = 'Inscription' if sub.asset_id in enrollment_ids else 'En cours'
            if sub.asset_id in enrollment_ids:
                program_title = sub.asset.program.name if sub.asset.program else ''
            elif sub.asset.step and sub.asset.step.degree and sub.asset.step.degree.program:
                program_title = sub.asset.step.degree.program.name
            else:
                program_title = ''

            writer.writerow([
                f'{sub.user.first_name} {sub.user.last_name}'.strip(),
                sub.user.phone or '',
                program_title,
                sub.asset.title,
                type_label,
                sub.submitted_at.strftime('%Y-%m-%d %H:%M'),
            ] + [resp_map.get(label, '') for label in all_labels])

        return response
