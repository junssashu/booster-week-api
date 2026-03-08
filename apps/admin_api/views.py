from rest_framework import viewsets

from apps.core.permissions import IsAdmin
from apps.programs.models import (
    Program, Degree, Step, Asset, QCMQuestion, FormFieldDef,
    DegreeFile, PriseDeContact, PriseDeContactAsset,
)
from .serializers import (
    AdminProgramSerializer, AdminDegreeSerializer, AdminStepSerializer,
    AdminAssetSerializer, AdminQCMQuestionSerializer, AdminFormFieldSerializer,
    AdminDegreeFileSerializer, AdminPriseDeContactSerializer, AdminPdcAssetSerializer,
)


class AdminProgramViewSet(viewsets.ModelViewSet):
    serializer_class = AdminProgramSerializer
    permission_classes = [IsAdmin]
    queryset = Program.objects.all().order_by('-created_at')


class AdminDegreeViewSet(viewsets.ModelViewSet):
    serializer_class = AdminDegreeSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = Degree.objects.all().order_by('order_index')
        program_id = self.request.query_params.get('programId')
        if program_id:
            qs = qs.filter(program_id=program_id)
        return qs


class AdminStepViewSet(viewsets.ModelViewSet):
    serializer_class = AdminStepSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = Step.objects.all().order_by('order_index')
        degree_id = self.request.query_params.get('degreeId')
        if degree_id:
            qs = qs.filter(degree_id=degree_id)
        return qs


class AdminAssetViewSet(viewsets.ModelViewSet):
    serializer_class = AdminAssetSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = Asset.objects.all().order_by('order_index')
        step_id = self.request.query_params.get('stepId')
        if step_id:
            qs = qs.filter(step_id=step_id)
        return qs


class AdminQCMQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = AdminQCMQuestionSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = QCMQuestion.objects.all().order_by('order_index')
        asset_id = self.request.query_params.get('assetId')
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs


class AdminFormFieldViewSet(viewsets.ModelViewSet):
    serializer_class = AdminFormFieldSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = FormFieldDef.objects.all().order_by('order_index')
        asset_id = self.request.query_params.get('assetId')
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs


class AdminDegreeFileViewSet(viewsets.ModelViewSet):
    serializer_class = AdminDegreeFileSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = DegreeFile.objects.all().order_by('order_index')
        degree_id = self.request.query_params.get('degreeId')
        if degree_id:
            qs = qs.filter(degree_id=degree_id)
        return qs


class AdminPriseDeContactViewSet(viewsets.ModelViewSet):
    serializer_class = AdminPriseDeContactSerializer
    permission_classes = [IsAdmin]
    queryset = PriseDeContact.objects.all().order_by('order_index')


class AdminPdcAssetViewSet(viewsets.ModelViewSet):
    serializer_class = AdminPdcAssetSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = PriseDeContactAsset.objects.all().order_by('order_index')
        pdc_id = self.request.query_params.get('priseDeContactId')
        if pdc_id:
            qs = qs.filter(prise_de_contact_id=pdc_id)
        return qs


# ===================================================================
# Additional admin views (sessions, users, enrollments, etc.)
# ===================================================================

from django.db.models import Q
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sessions.models import LiveReplaySession
from apps.accounts.models import User
from apps.enrollments.models import Enrollment, Payment, PromoCode
from apps.testimonies.models import Testimony
from apps.content.models import FAQItem, ContactInfo, ContactSubmission
from .serializers import (
    AdminSessionSerializer, AdminUserSerializer, AdminEnrollmentSerializer,
    AdminPaymentSerializer, AdminTestimonySerializer, AdminFAQSerializer,
    AdminContactInfoSerializer, AdminContactSubmissionSerializer,
    AdminPromoCodeSerializer,
)


# ---------------------------------------------------------------------------
# Sessions — full CRUD
# ---------------------------------------------------------------------------

class AdminSessionViewSet(viewsets.ModelViewSet):
    serializer_class = AdminSessionSerializer
    permission_classes = [IsAdmin]
    queryset = LiveReplaySession.objects.all().order_by('-date')


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
    permission_classes = [IsAdmin]

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


# ---------------------------------------------------------------------------
# Enrollments — list (filterable by status, program)
# ---------------------------------------------------------------------------

class AdminEnrollmentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminEnrollmentSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = Enrollment.objects.select_related('user', 'program').order_by('-created_at')
        payment_status = self.request.query_params.get('status')
        if payment_status:
            qs = qs.filter(payment_status=payment_status)
        program_id = self.request.query_params.get('programId')
        if program_id:
            qs = qs.filter(program_id=program_id)
        return qs


# ---------------------------------------------------------------------------
# Payments — list (filterable by status, method)
# ---------------------------------------------------------------------------

class AdminPaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminPaymentSerializer
    permission_classes = [IsAdmin]

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
# Testimonies — list + delete (moderation)
# ---------------------------------------------------------------------------

class AdminTestimonyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminTestimonySerializer
    permission_classes = [IsAdmin]
    queryset = Testimony.objects.select_related('author').order_by('-created_at')


# ---------------------------------------------------------------------------
# FAQ — full CRUD
# ---------------------------------------------------------------------------

class AdminFAQViewSet(viewsets.ModelViewSet):
    serializer_class = AdminFAQSerializer
    permission_classes = [IsAdmin]
    queryset = FAQItem.objects.all().order_by('order_index')


# ---------------------------------------------------------------------------
# Contact Info — singleton GET / PUT
# ---------------------------------------------------------------------------

class AdminContactInfoView(APIView):
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]
    queryset = ContactSubmission.objects.all().order_by('-created_at')


# ---------------------------------------------------------------------------
# Promo Codes — list (read-only)
# ---------------------------------------------------------------------------

class AdminPromoCodeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminPromoCodeSerializer
    permission_classes = [IsAdmin]
    queryset = PromoCode.objects.select_related('creator').order_by('-created_at')


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
    permission_classes = [IsAdmin]
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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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
