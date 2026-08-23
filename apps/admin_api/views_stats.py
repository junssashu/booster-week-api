from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminOrAssistant
from apps.accounts.models import User
from apps.enrollments.models import Enrollment, Payment


class AdminStatsOverviewView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        from apps.programs.models import Program as ProgramModel

        total_users = User.objects.filter(role='user').count()
        total_enrollments = Enrollment.objects.count()
        total_revenue = (
            Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        )
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
            {'date': str(t['date']), 'count': t['count'] or 0}
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
            {'date': str(t['date']), 'amount': t['amount'] or 0}
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
