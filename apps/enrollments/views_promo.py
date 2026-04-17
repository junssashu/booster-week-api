from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PromoCode, PromoCodeRedemption
from .serializers import PromoCodeSerializer, PromoCodeValidateSerializer


class PromoCodeGenerateView(APIView):
    """Generate a promo code. Admin only."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only administrators can generate promo codes.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        promo = PromoCode.objects.create(
            creator=request.user,
            discount_percent=20,
            max_uses=1,
            expires_at=timezone.now() + timedelta(days=30),
        )
        return Response(PromoCodeSerializer(promo).data, status=status.HTTP_201_CREATED)


class PromoCodeValidateView(APIView):
    """Validate a promo code and return discount info."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PromoCodeValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code'].upper()
        try:
            promo = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Code promo invalide.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not promo.is_valid:
            return Response(
                {'valid': False, 'error': 'Code promo expire ou deja utilise.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        already_used = PromoCodeRedemption.objects.filter(
            promo_code=promo, user=request.user
        ).exists()
        if already_used:
            return Response(
                {'valid': False, 'error': 'Vous avez deja utilise ce code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'valid': True,
            'code': promo.code,
            'discountPercent': promo.discount_percent,
        })


class PromoCodeListView(APIView):
    """List promo codes created by the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        codes = PromoCode.objects.filter(creator=request.user).order_by('-created_at')
        return Response(PromoCodeSerializer(codes, many=True).data)
