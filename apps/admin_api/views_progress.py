import csv

from django.db.models import Avg
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminOrAssistant
from apps.enrollments.models import Enrollment
from apps.progress.models import StepProgress, QCMAttempt, FormSubmission
from .serializers import (
    AdminStepProgressSerializer, AdminQCMAttemptSerializer, AdminFormSubmissionSerializer,
)


class AdminUserProgressView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request, user_id):
        program_id = request.query_params.get('programId')
        if not program_id:
            return Response({'error': 'programId required'}, status=400)

        step_progress = StepProgress.objects.filter(
            user_id=user_id, program_id=program_id
        ).select_related('step__degree').order_by(
            'step__degree__order_index', 'step__order_index'
        )

        qcm_attempts = QCMAttempt.objects.filter(
            user_id=user_id, asset__step__degree__program_id=program_id
        ).select_related('asset').order_by('-attempted_at')[:50]

        form_submissions = FormSubmission.objects.filter(
            user_id=user_id, asset__step__degree__program_id=program_id
        ).select_related('asset').order_by('-submitted_at')[:50]

        degrees = {}
        for sp in step_progress:
            deg_id = sp.step.degree.id
            if deg_id not in degrees:
                degrees[deg_id] = {
                    'degreeId': deg_id,
                    'degreeTitle': sp.step.degree.title,
                    'steps': [],
                }
            degrees[deg_id]['steps'].append(AdminStepProgressSerializer(sp).data)

        return Response({'data': {
            'degrees': list(degrees.values()),
            'qcmAttempts': AdminQCMAttemptSerializer(qcm_attempts, many=True).data,
            'formSubmissions': AdminFormSubmissionSerializer(form_submissions, many=True).data,
        }})


class AdminProgressStatsView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        program_id = request.query_params.get('programId')
        if not program_id:
            return Response({'error': 'programId required'}, status=400)

        from apps.programs.models import Degree

        degrees = Degree.objects.filter(program_id=program_id).order_by('order_index')

        funnel = []
        for degree in degrees:
            student_count = StepProgress.objects.filter(
                program_id=program_id,
                step__degree=degree,
                completion_percentage__gte=70,
            ).values('user').distinct().count()

            avg_score = QCMAttempt.objects.filter(
                asset__step__degree=degree,
            ).aggregate(avg=Avg('score'))['avg']

            funnel.append({
                'degreeId': degree.id,
                'degreeTitle': degree.title,
                'orderIndex': degree.order_index,
                'studentCount': student_count,
                'avgQcmScore': round(avg_score, 1) if avg_score else None,
            })

        total_enrolled = Enrollment.objects.filter(program_id=program_id).count()

        return Response({'data': {
            'totalEnrolled': total_enrolled,
            'funnel': funnel,
        }})


class AdminProgressExportView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        program_id = request.query_params.get('programId')
        if not program_id:
            return Response({'error': 'programId required'}, status=400)

        progress = StepProgress.objects.filter(
            program_id=program_id
        ).select_related('user', 'step__degree').order_by(
            'user__last_name', 'step__degree__order_index', 'step__order_index'
        )

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="progress-{program_id}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Etudiant', 'Telephone', 'Degre', 'Etape', 'Statut', 'Completion %', 'Derniere MAJ'])
        for sp in progress:
            writer.writerow([
                f'{sp.user.first_name} {sp.user.last_name}',
                sp.user.phone,
                sp.step.degree.title,
                sp.step.title,
                sp.status,
                sp.completion_percentage,
                sp.updated_at.isoformat(),
            ])
        return response
