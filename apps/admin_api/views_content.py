from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminOrAssistant, IsAdminOnly
from apps.testimonies.models import Testimony, TestimonyComment
from apps.content.models import FAQItem, ContactInfo, ContactSubmission, AppSettings
from apps.enrollments.models import PromoCode
from .serializers import (
    AdminTestimonySerializer, AdminFAQSerializer,
    AdminContactInfoSerializer, AdminContactSubmissionSerializer,
    AdminPromoCodeSerializer, AdminAppSettingsSerializer,
    AdminTestimonyCommentSerializer,
)


class AdminTestimonyViewSet(viewsets.ModelViewSet):
    serializer_class = AdminTestimonySerializer
    permission_classes = [IsAdminOrAssistant]
    queryset = Testimony.objects.select_related('author').prefetch_related(
        'comments__author'
    ).order_by('-created_at')


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


class AdminFAQViewSet(viewsets.ModelViewSet):
    serializer_class = AdminFAQSerializer
    permission_classes = [IsAdminOrAssistant]
    queryset = FAQItem.objects.all().order_by('order_index')


class AdminContactInfoView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        info, _created = ContactInfo.objects.get_or_create(id=1, defaults={
            'phone': '', 'email': '', 'whatsapp': '',
        })
        serializer = AdminContactInfoSerializer(info)
        return Response(serializer.data)

    def put(self, request):
        info, _created = ContactInfo.objects.get_or_create(id=1, defaults={
            'phone': '', 'email': '', 'whatsapp': '',
        })
        serializer = AdminContactInfoSerializer(info, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminContactSubmissionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminContactSubmissionSerializer
    permission_classes = [IsAdminOrAssistant]
    queryset = ContactSubmission.objects.all().order_by('-created_at')


class AdminPromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.select_related('creator').order_by('-created_at')
    serializer_class = AdminPromoCodeSerializer
    permission_classes = [IsAdminOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


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
