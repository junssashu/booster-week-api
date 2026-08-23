from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.core.permissions import IsAdminOrAssistant
from .serializers import AdminMandataireSerializer


class AdminMandataireListView(APIView):
    permission_classes = [IsAdminOrAssistant]

    def get(self, request):
        qs = (
            User.objects.filter(is_mandataire=True)
            .annotate(
                enrollment_count=Count('mandated_enrollments'),
                total_revenue=Coalesce(Sum('mandated_enrollments__amount_paid'), 0),
            )
            .prefetch_related('mandated_enrollments__program')
            .order_by('first_name', 'last_name')
        )
        serializer = AdminMandataireSerializer(qs, many=True)
        return Response(serializer.data)
