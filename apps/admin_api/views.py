import logging

from rest_framework import viewsets

logger = logging.getLogger(__name__)

from apps.core.permissions import IsAdminOrAssistant, IsAdminOnly, IsAdminOrAssistantReadOnly
from apps.programs.models import (
    Program, Degree, Step, Asset, QCMQuestion, FormFieldDef,
    DegreeFile, PriseDeContact, PriseDeContactAsset,
)
from .serializers import (
    AdminProgramSerializer, AdminProgramDetailSerializer,
    AdminDegreeSerializer, AdminDegreeDetailSerializer,
    AdminStepSerializer, AdminStepDetailSerializer,
    AdminAssetSerializer, AdminQCMQuestionSerializer, AdminFormFieldSerializer,
    AdminDegreeFileSerializer, AdminPriseDeContactSerializer, AdminPdcAssetSerializer,
)


class AdminProgramViewSet(viewsets.ModelViewSet):
    serializer_class = AdminProgramSerializer
    permission_classes = [IsAdminOrAssistantReadOnly]
    queryset = Program.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminProgramDetailSerializer
        return AdminProgramSerializer


class AdminDegreeViewSet(viewsets.ModelViewSet):
    serializer_class = AdminDegreeSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminDegreeDetailSerializer
        return AdminDegreeSerializer

    def get_queryset(self):
        qs = Degree.objects.all().order_by('order_index')
        program_id = self.request.query_params.get('programId')
        if program_id:
            qs = qs.filter(program_id=program_id)
        return qs

    def perform_destroy(self, instance):
        from apps.progress.models import StepProgress, AssetCompletion, QCMAttempt, FormSubmission
        steps = instance.steps.all()
        assets = Asset.objects.filter(step__in=steps)
        StepProgress.objects.filter(step__in=steps).delete()
        AssetCompletion.objects.filter(asset__in=assets).delete()
        QCMAttempt.objects.filter(asset__in=assets).delete()
        FormSubmission.objects.filter(asset__in=assets).delete()
        instance.delete()


class AdminStepViewSet(viewsets.ModelViewSet):
    serializer_class = AdminStepSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminStepDetailSerializer
        return AdminStepSerializer

    def get_queryset(self):
        qs = Step.objects.all().order_by('order_index')
        degree_id = self.request.query_params.get('degreeId')
        if degree_id:
            qs = qs.filter(degree_id=degree_id)
        return qs

    def perform_destroy(self, instance):
        from apps.progress.models import StepProgress, AssetCompletion, QCMAttempt, FormSubmission
        assets = instance.assets.all()
        StepProgress.objects.filter(step=instance).delete()
        AssetCompletion.objects.filter(asset__in=assets).delete()
        QCMAttempt.objects.filter(asset__in=assets).delete()
        FormSubmission.objects.filter(asset__in=assets).delete()
        instance.delete()


class AdminAssetViewSet(viewsets.ModelViewSet):
    serializer_class = AdminAssetSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = Asset.objects.all().order_by('order_index')
        step_id = self.request.query_params.get('stepId')
        if step_id:
            qs = qs.filter(step_id=step_id)
        return qs

    def perform_create(self, serializer):
        asset = serializer.save()
        self._save_nested(asset, self.request.data)

    def perform_update(self, serializer):
        asset = serializer.save()
        self._save_nested(asset, self.request.data)

    def _save_nested(self, asset, data):
        """Save nested QCM questions and form fields from request payload."""
        from apps.programs.models import QCMQuestion, FormFieldDef

        # Handle QCM questions
        questions = data.get('questions')
        if questions is not None and asset.type == 'qcm':
            # Delete existing and recreate (simpler than diffing)
            asset.questions.all().delete()
            for i, q in enumerate(questions):
                QCMQuestion.objects.create(
                    asset=asset,
                    question=q.get('question', ''),
                    options=q.get('options', []),
                    correct_index=q.get('correctIndex', 0),
                    order_index=q.get('index', i),
                )

        # Handle form fields
        form_fields = data.get('formFields')
        if form_fields is not None and asset.type == 'form':
            asset.form_fields.all().delete()
            for i, f in enumerate(form_fields):
                FormFieldDef.objects.create(
                    id=f.get('id', f'field_{asset.id}_{i}'),
                    asset=asset,
                    label=f.get('label', ''),
                    type=f.get('type', 'text'),
                    required=f.get('required', False),
                    select_options=f.get('selectOptions'),
                    order_index=f.get('orderIndex', i),
                )


class AdminQCMQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = AdminQCMQuestionSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = QCMQuestion.objects.all().order_by('order_index')
        asset_id = self.request.query_params.get('assetId')
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs


class AdminFormFieldViewSet(viewsets.ModelViewSet):
    serializer_class = AdminFormFieldSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = FormFieldDef.objects.all().order_by('order_index')
        asset_id = self.request.query_params.get('assetId')
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs


class AdminDegreeFileViewSet(viewsets.ModelViewSet):
    serializer_class = AdminDegreeFileSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = DegreeFile.objects.all().order_by('order_index')
        degree_id = self.request.query_params.get('degreeId')
        if degree_id:
            qs = qs.filter(degree_id=degree_id)
        return qs


class AdminPriseDeContactViewSet(viewsets.ModelViewSet):
    serializer_class = AdminPriseDeContactSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = PriseDeContact.objects.all().order_by('order_index')
        program_id = self.request.query_params.get('programId')
        degree_id = self.request.query_params.get('degreeId')
        step_id = self.request.query_params.get('stepId')
        if program_id:
            qs = qs.filter(program_id=program_id)
        if degree_id:
            qs = qs.filter(degree_id=degree_id)
        if step_id:
            qs = qs.filter(step_id=step_id)
        return qs


class AdminPdcAssetViewSet(viewsets.ModelViewSet):
    serializer_class = AdminPdcAssetSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = PriseDeContactAsset.objects.all().order_by('order_index')
        pdc_id = self.request.query_params.get('priseDeContactId')
        if pdc_id:
            qs = qs.filter(prise_de_contact_id=pdc_id)
        return qs


# ===================================================================
# Additional admin views (sessions, users, enrollments, etc.)
# ===================================================================

from django.db.models import Count, Q
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sessions.models import LiveReplaySession, SessionAttendance
from apps.accounts.models import User
from apps.enrollments.models import Enrollment, Payment, PromoCode
from apps.testimonies.models import Testimony, TestimonyComment
from apps.content.models import FAQItem, ContactInfo, ContactSubmission, AppSettings
from .serializers import (
    AdminSessionSerializer, AdminUserSerializer, AdminEnrollmentSerializer,
    AdminEnrollmentWriteSerializer,
    AdminPaymentSerializer, AdminTestimonySerializer, AdminFAQSerializer,
    AdminContactInfoSerializer, AdminContactSubmissionSerializer,
    AdminPromoCodeSerializer,
    AdminAppSettingsSerializer,
    AdminTestimonyCommentSerializer,
    AdminSessionAttendanceSerializer,
    AdminStepProgressSerializer, AdminQCMAttemptSerializer, AdminFormSubmissionSerializer,
)


# ---------------------------------------------------------------------------
# Sessions — full CRUD
# ---------------------------------------------------------------------------

class AdminSessionViewSet(viewsets.ModelViewSet):
    serializer_class = AdminSessionSerializer
    permission_classes = [IsAdminOrAssistant]
    queryset = LiveReplaySession.objects.all().order_by('-date')

    def get_queryset(self):
        return super().get_queryset().annotate(attendance_count=Count('attendances'))

    @action(detail=True, methods=['get'], url_path='attendance')
    def attendance(self, request, pk=None):
        session = self.get_object()
        attendances = SessionAttendance.objects.filter(session=session).select_related('user').order_by('-joined_at')
        serializer = AdminSessionAttendanceSerializer(attendances, many=True)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['get'], url_path='attendance/export')
    def attendance_export(self, request, pk=None):
        import csv
        from django.http import HttpResponse
        session = self.get_object()
        attendances = SessionAttendance.objects.filter(session=session).select_related('user').order_by('-joined_at')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance-{session.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Prenom', 'Nom', 'Telephone', 'Date'])
        for a in attendances:
            writer.writerow([a.user.first_name, a.user.last_name, a.user.phone, a.joined_at.isoformat()])
        return response


# ---------------------------------------------------------------------------
# Users — list (searchable), retrieve, partial update (role only)
# ---------------------------------------------------------------------------

class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = User.objects.all().order_by('-created_at')
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
            )
        return qs

    @action(detail=True, methods=['post'], url_path='reset')
    def reset_user(self, request, pk=None):
        """Reset all data for a user: enrollments, payments, progress, promo codes, testimonies."""
        user = self.get_object()

        from apps.enrollments.models import Enrollment, Payment, PromoCodeRedemption
        from apps.progress.models import (
            StepProgress, AssetCompletion, QCMAttempt, FormSubmission,
            PriseDeContactAcceptance, ConsigneAcceptance,
        )
        from apps.testimonies.models import Testimony, TestimonyReaction, TestimonyComment

        counts = {}

        # Progress
        counts['stepProgress'] = StepProgress.objects.filter(user=user).delete()[0]
        counts['assetCompletions'] = AssetCompletion.objects.filter(user=user).delete()[0]
        counts['qcmAttempts'] = QCMAttempt.objects.filter(user=user).delete()[0]
        counts['formSubmissions'] = FormSubmission.objects.filter(user=user).delete()[0]
        counts['pdcAcceptances'] = PriseDeContactAcceptance.objects.filter(user=user).delete()[0]
        counts['consigneAcceptances'] = ConsigneAcceptance.objects.filter(user=user).delete()[0]

        # Payments (delete before enrollments to avoid FK issues)
        counts['payments'] = Payment.objects.filter(enrollment__user=user).delete()[0]
        counts['promoRedemptions'] = PromoCodeRedemption.objects.filter(user=user).delete()[0]

        # Enrollments
        counts['enrollments'] = Enrollment.objects.filter(user=user).delete()[0]

        # Testimonies (optional — user content)
        counts['reactions'] = TestimonyReaction.objects.filter(user=user).delete()[0]
        counts['comments'] = TestimonyComment.objects.filter(author=user).delete()[0]
        counts['testimonies'] = Testimony.objects.filter(author=user).delete()[0]

        logger.info('Admin reset user %s: %s', user.id, counts)

        return Response({
            'data': {
                'userId': user.id,
                'userName': f'{user.first_name} {user.last_name}',
                'deleted': counts,
            }
        })


# ---------------------------------------------------------------------------
# Enrollments — list (filterable by status, program)
# ---------------------------------------------------------------------------

class AdminEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.select_related('user', 'program', 'mandataire').order_by('-created_at')
    permission_classes = [IsAdminOrAssistantReadOnly]

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return AdminEnrollmentWriteSerializer
        return AdminEnrollmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.query_params.get('status')
        program_id = self.request.query_params.get('programId')
        user_id = self.request.query_params.get('userId')
        if status:
            qs = qs.filter(payment_status=status)
        if program_id:
            qs = qs.filter(program_id=program_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        mandataire_id = self.request.query_params.get('mandataireId')
        if mandataire_id == 'none':
            qs = qs.filter(mandataire__isnull=True)
        elif mandataire_id:
            qs = qs.filter(mandataire_id=mandataire_id)
        return qs

    def perform_destroy(self, instance):
        from apps.enrollments.views import _cleanup_enrollment_progress
        _cleanup_enrollment_progress(instance.user, instance.program)
        if instance.payments.exists():
            instance.payment_status = 'cancelled'
            instance.save(update_fields=['payment_status'])
        else:
            instance.delete()

    @action(detail=True, methods=['get'], url_path='invoice')
    def invoice(self, request, pk=None):
        enrollment = self.get_object()
        payments = enrollment.payments.filter(status='completed').order_by('date')
        return Response({'data': {
            'invoiceNumber': f'BWC-{enrollment.id.upper()}-{enrollment.created_at.strftime("%Y%m%d")}',
            'student': {
                'name': f'{enrollment.user.first_name} {enrollment.user.last_name}',
                'phone': enrollment.user.phone,
                'email': enrollment.user.email,
            },
            'program': {
                'name': enrollment.program.name,
                'price': enrollment.program.price,
            },
            'enrollment': {
                'id': enrollment.id,
                'paymentType': enrollment.payment_type,
                'paymentStatus': enrollment.payment_status,
                'amountPaid': enrollment.amount_paid,
                'totalAmount': enrollment.total_amount,
                'enrollmentDate': enrollment.enrollment_date,
            },
            'payments': [{
                'amount': p.amount,
                'method': p.method,
                'date': p.date,
                'transactionRef': p.transaction_ref,
            } for p in payments],
        }})


# ---------------------------------------------------------------------------
# Payments — list (filterable by status, method)
# ---------------------------------------------------------------------------

class AdminPaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminPaymentSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = Payment.objects.select_related(
            'enrollment', 'enrollment__user', 'enrollment__program',
        ).order_by('-created_at')
        payment_status = self.request.query_params.get('status')
        if payment_status:
            qs = qs.filter(status=payment_status)
        method = self.request.query_params.get('method')
        if method:
            qs = qs.filter(method=method)
        return qs


# ---------------------------------------------------------------------------
# Testimonies — full CRUD (admin)
# ---------------------------------------------------------------------------

class AdminTestimonyViewSet(viewsets.ModelViewSet):
    serializer_class = AdminTestimonySerializer
    permission_classes = [IsAdminOrAssistant]
    queryset = Testimony.objects.select_related('author').prefetch_related('comments__author').order_by('-created_at')


# ---------------------------------------------------------------------------
# Testimony Comments — list + delete + bulk-delete (moderation)
# ---------------------------------------------------------------------------

class AdminTestimonyCommentViewSet(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = TestimonyComment.objects.select_related('author', 'testimony').order_by('-created_at')
    serializer_class = AdminTestimonyCommentSerializer
    permission_classes = [IsAdminOrAssistant]

    def get_queryset(self):
        qs = super().get_queryset()
        testimony_id = self.request.query_params.get('testimonyId')
        if testimony_id:
            qs = qs.filter(testimony_id=testimony_id)
        return qs

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        deleted, _ = TestimonyComment.objects.filter(id__in=ids).delete()
        return Response({'deleted': deleted})


# ---------------------------------------------------------------------------
# FAQ — full CRUD
# ---------------------------------------------------------------------------

class AdminFAQViewSet(viewsets.ModelViewSet):
    serializer_class = AdminFAQSerializer
    permission_classes = [IsAdminOrAssistant]
    queryset = FAQItem.objects.all().order_by('order_index')


# ---------------------------------------------------------------------------
# Contact Info — singleton GET / PUT
# ---------------------------------------------------------------------------

class AdminContactInfoView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        info, _created = ContactInfo.objects.get_or_create(id=1, defaults={
            'phone': '',
            'email': '',
            'whatsapp': '',
        })
        serializer = AdminContactInfoSerializer(info)
        return Response(serializer.data)

    def put(self, request):
        info, _created = ContactInfo.objects.get_or_create(id=1, defaults={
            'phone': '',
            'email': '',
            'whatsapp': '',
        })
        serializer = AdminContactInfoSerializer(info, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Contact Submissions — list + delete
# ---------------------------------------------------------------------------

class AdminContactSubmissionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminContactSubmissionSerializer
    permission_classes = [IsAdminOrAssistant]
    queryset = ContactSubmission.objects.all().order_by('-created_at')


# ---------------------------------------------------------------------------
# Promo Codes — full CRUD
# ---------------------------------------------------------------------------

class AdminPromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.select_related('creator').order_by('-created_at')
    serializer_class = AdminPromoCodeSerializer
    permission_classes = [IsAdminOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


# ---------------------------------------------------------------------------
# App Settings — singleton GET / PUT
# ---------------------------------------------------------------------------

class AdminAppSettingsView(APIView):
    permission_classes = [IsAdminOnly]

    def get(self, request):
        settings, _ = AppSettings.objects.get_or_create(id=1)
        serializer = AdminAppSettingsSerializer(settings)
        return Response({'data': serializer.data})

    def put(self, request):
        settings, _ = AppSettings.objects.get_or_create(id=1)
        serializer = AdminAppSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': serializer.data})


# ===================================================================
# File Upload
# ===================================================================

import io
import os
import uuid

from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from minio import Minio

from apps.core.storage import resolve_url


def _get_minio_client():
    endpoint = (
        f"{settings.MINIO_ENDPOINT}:{settings.MINIO_PORT}"
        if settings.MINIO_PORT not in (80, 443)
        else settings.MINIO_ENDPOINT
    )
    return Minio(
        endpoint,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )


class AdminFileUploadView(APIView):
    permission_classes = [IsAdminOrAssistant]
    parser_classes = [MultiPartParser, FormParser]

    ALLOWED_TYPES = {
        'audio': ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac'],
        'document': ['application/pdf'],
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        'video': ['video/mp4', 'video/webm', 'video/quicktime'],
    }
    MAX_SIZE = 50 * 1024 * 1024  # 50MB

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)

        bucket = request.data.get('bucket', 'documents')
        folder = request.data.get('folder', '')

        if file.size > self.MAX_SIZE:
            return Response({'error': 'File too large (max 50MB)'}, status=400)

        # Validate file type
        content_type = file.content_type
        allowed = []
        for types in self.ALLOWED_TYPES.values():
            allowed.extend(types)
        if content_type not in allowed:
            return Response({'error': f'File type {content_type} not allowed'}, status=400)

        # Upload to MinIO
        try:
            client = _get_minio_client()

            ext = file.name.rsplit('.', 1)[-1] if '.' in file.name else ''
            filename = f"{uuid.uuid4().hex[:12]}.{ext}" if ext else uuid.uuid4().hex[:12]
            object_name = f"{folder}/{filename}" if folder else filename

            file_data = file.read()
            client.put_object(
                bucket,
                object_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )

            # Build public URL using the project's resolve_url helper
            minio_ref = f"minio://{bucket}/{object_name}"
            url = resolve_url(minio_ref)

            return Response({'data': {'url': url, 'filename': filename}})
        except Exception as e:
            return Response({'error': f'Upload failed: {str(e)}'}, status=500)


# ===================================================================
# Analytics / Stats
# ===================================================================

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta


class AdminStatsOverviewView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        from apps.programs.models import Program as ProgramModel

        total_users = User.objects.filter(role='user').count()
        total_enrollments = Enrollment.objects.count()
        total_revenue = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount'))['total'] or 0
        active_programs = ProgramModel.objects.filter(is_active=True).count()

        return Response({'data': {
            'totalUsers': total_users,
            'totalEnrollments': total_enrollments,
            'totalRevenue': total_revenue,
            'activePrograms': active_programs,
        }})


class AdminEnrollmentTrendsView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)

        trends = (
            Enrollment.objects
            .filter(created_at__gte=since)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        return Response({'data': [
            {'date': str(t['date']), 'count': t['count']}
            for t in trends
        ]})


class AdminRevenueTrendsView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)

        trends = (
            Payment.objects
            .filter(status='completed', created_at__gte=since)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(amount=Sum('amount'))
            .order_by('date')
        )

        return Response({'data': [
            {'date': str(t['date']), 'amount': t['amount']}
            for t in trends
        ]})


class AdminCompletionStatsView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        from apps.programs.models import Program as ProgramModel

        programs = ProgramModel.objects.filter(is_active=True)
        stats = []
        for prog in programs:
            enrolled = Enrollment.objects.filter(program=prog).count()
            completed = Enrollment.objects.filter(
                program=prog, payment_status='completed'
            ).count()
            rate = (completed / enrolled * 100) if enrolled > 0 else 0
            stats.append({
                'programName': prog.name,
                'enrolledCount': enrolled,
                'completedCount': completed,
                'completionRate': round(rate, 1),
            })

        return Response({'data': stats})


# ---------------------------------------------------------------------------
# Progress Tracking
# ---------------------------------------------------------------------------

from django.db.models import Avg
from apps.progress.models import StepProgress, QCMAttempt, FormSubmission


class AdminUserProgressView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request, user_id):
        program_id = request.query_params.get('programId')
        if not program_id:
            return Response({'error': 'programId required'}, status=400)

        step_progress = StepProgress.objects.filter(
            user_id=user_id, program_id=program_id
        ).select_related('step__degree').order_by('step__degree__order_index', 'step__order_index')

        qcm_attempts = QCMAttempt.objects.filter(
            user_id=user_id, asset__step__degree__program_id=program_id
        ).select_related('asset').order_by('-attempted_at')[:50]

        form_submissions = FormSubmission.objects.filter(
            user_id=user_id, asset__step__degree__program_id=program_id
        ).select_related('asset').order_by('-submitted_at')[:50]

        # Group step progress by degree
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
        import csv
        from django.http import HttpResponse

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
