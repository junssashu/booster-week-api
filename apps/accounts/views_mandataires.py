from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User


class PublicMandataireListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = (
            User.objects
            .filter(is_mandataire=True)
            .order_by('first_name', 'last_name')
            .values('id', 'first_name', 'last_name')
        )
        data = [
            {'id': u['id'], 'firstName': u['first_name'], 'lastName': u['last_name']}
            for u in qs
        ]
        return Response(data)
