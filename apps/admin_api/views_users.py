import logging

from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrAssistant, IsAdminOnly
from apps.accounts.models import User
from .serializers import AdminUserSerializer

logger = logging.getLogger(__name__)


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

    @action(detail=True, methods=['patch'], url_path='set-mandataire',
            permission_classes=[IsAdminOnly])
    def set_mandataire(self, request, pk=None):
        user = self.get_object()
        is_mandataire = request.data.get('is_mandataire')
        if not isinstance(is_mandataire, bool):
            return Response(
                {'error': 'is_mandataire must be a boolean'}, status=400
            )
        user.is_mandataire = is_mandataire
        user.save(update_fields=['is_mandataire'])
        return Response({'id': user.id, 'isMandataire': user.is_mandataire})

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

        counts['stepProgress'] = StepProgress.objects.filter(user=user).delete()[0]
        counts['assetCompletions'] = AssetCompletion.objects.filter(user=user).delete()[0]
        counts['qcmAttempts'] = QCMAttempt.objects.filter(user=user).delete()[0]
        counts['formSubmissions'] = FormSubmission.objects.filter(user=user).delete()[0]
        counts['pdcAcceptances'] = PriseDeContactAcceptance.objects.filter(user=user).delete()[0]
        counts['consigneAcceptances'] = ConsigneAcceptance.objects.filter(user=user).delete()[0]

        counts['payments'] = Payment.objects.filter(enrollment__user=user).delete()[0]
        counts['promoRedemptions'] = PromoCodeRedemption.objects.filter(user=user).delete()[0]
        counts['enrollments'] = Enrollment.objects.filter(user=user).delete()[0]

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
