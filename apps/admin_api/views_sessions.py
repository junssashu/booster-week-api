import csv

from django.db.models import Count
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrAssistant
from apps.sessions.models import LiveReplaySession, SessionAttendance
from .serializers import AdminSessionSerializer, AdminSessionAttendanceSerializer


class AdminSessionViewSet(viewsets.ModelViewSet):
    serializer_class = AdminSessionSerializer
    permission_classes = [IsAdminOrAssistant]
    queryset = LiveReplaySession.objects.all().order_by('-date')

    def get_queryset(self):
        qs = super().get_queryset().annotate(attendance_count=Count('attendances'))
        program_id = self.request.query_params.get('programId')
        if program_id:
            qs = qs.filter(program_id=program_id)
        return qs

    @action(detail=True, methods=['get'], url_path='attendance')
    def attendance(self, request, pk=None):
        session = self.get_object()
        attendances = SessionAttendance.objects.filter(
            session=session
        ).select_related('user').order_by('-joined_at')
        serializer = AdminSessionAttendanceSerializer(attendances, many=True)
        return Response({'data': serializer.data})

    @action(detail=True, methods=['get'], url_path='attendance/export')
    def attendance_export(self, request, pk=None):
        session = self.get_object()
        attendances = SessionAttendance.objects.filter(
            session=session
        ).select_related('user').order_by('-joined_at')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="attendance-{session.id}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(['Prenom', 'Nom', 'Telephone', 'Date'])
        for a in attendances:
            writer.writerow([
                a.user.first_name,
                a.user.last_name,
                a.user.phone,
                a.joined_at.isoformat(),
            ])
        return response
