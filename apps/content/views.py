from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ContactInfo, FAQItem


class FAQView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Content'],
        summary='List all FAQ items',
        description=(
            'Return all frequently asked questions ordered by their display index. '
            'No authentication required.'
        ),
        responses={
            200: inline_serializer(
                name='FAQListResponse',
                fields={
                    'data': drf_serializers.ListField(
                        child=inline_serializer(
                            name='FAQItem',
                            fields={
                                'id': drf_serializers.CharField(),
                                'question': drf_serializers.CharField(),
                                'answer': drf_serializers.CharField(),
                                'orderIndex': drf_serializers.IntegerField(),
                            },
                        ),
                        help_text='List of FAQ items ordered by display index.',
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='FAQ list response',
                response_only=True,
                status_codes=['200'],
                value={
                    'data': [
                        {
                            'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                            'question': 'Comment fonctionne Booster Week ?',
                            'answer': 'Booster Week vous permet de...',
                            'orderIndex': 1,
                        },
                        {
                            'id': 'b2c3d4e5-f6a7-8901-bcde-f12345678901',
                            'question': 'Comment contacter le support ?',
                            'answer': 'Vous pouvez nous contacter via...',
                            'orderIndex': 2,
                        },
                    ]
                },
            ),
        ],
    )
    def get(self, request):
        items = FAQItem.objects.all().order_by('order_index')
        data = [
            {
                'id': str(item.id),
                'question': item.question,
                'answer': item.answer,
                'orderIndex': item.order_index,
            }
            for item in items
        ]
        return Response({'data': data})


class ContactView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Content'],
        summary='Get contact information',
        description=(
            'Return the application contact details (phone, email, WhatsApp). '
            'Returns empty strings if no contact information has been configured. '
            'No authentication required.'
        ),
        responses={
            200: inline_serializer(
                name='ContactInfoResponse',
                fields={
                    'data': inline_serializer(
                        name='ContactInfoData',
                        fields={
                            'phone': drf_serializers.CharField(
                                help_text='Support phone number.',
                            ),
                            'email': drf_serializers.EmailField(
                                help_text='Support email address.',
                            ),
                            'whatsapp': drf_serializers.CharField(
                                help_text='WhatsApp contact number.',
                            ),
                        },
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Contact info response',
                response_only=True,
                status_codes=['200'],
                value={
                    'data': {
                        'phone': '+2250700000000',
                        'email': 'support@boosterweek.ci',
                        'whatsapp': '+2250700000000',
                    }
                },
            ),
            OpenApiExample(
                name='No contact info configured',
                response_only=True,
                status_codes=['200'],
                value={
                    'data': {
                        'phone': '',
                        'email': '',
                        'whatsapp': '',
                    }
                },
            ),
        ],
    )
    def get(self, request):
        info = ContactInfo.objects.filter(id=1).first()
        if not info:
            return Response({'data': {
                'phone': '',
                'email': '',
                'whatsapp': '',
            }})

        return Response({
            'data': {
                'phone': info.phone,
                'email': info.email,
                'whatsapp': info.whatsapp,
            }
        })
