from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.views import APIView

from apps.content.models import AppSettings
from apps.core.storage import resolve_url


class AppConfigView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Config'],
        summary='Get app configuration',
        description=(
            'Return public application configuration values. '
            'No authentication required.'
        ),
        responses={
            200: inline_serializer(
                name='AppConfigResponse',
                fields={
                    'data': inline_serializer(
                        name='AppConfigData',
                        fields={
                            'backgroundMusicUrl': drf_serializers.URLField(
                                help_text='URL of the background music track.',
                            ),
                        },
                    ),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='App config response',
                response_only=True,
                status_codes=['200'],
                value={
                    'data': {
                        'backgroundMusicUrl': (
                            'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3'
                        ),
                    }
                },
            ),
        ],
    )
    def get(self, request):
        app_settings, _ = AppSettings.objects.get_or_create(id=1)
        music_url = resolve_url(app_settings.background_music_url or settings.BACKGROUND_MUSIC_URL)
        video_url = resolve_url(app_settings.presentation_video_url) if app_settings.presentation_video_url else ''
        return Response({
            'data': {
                'backgroundMusicUrl': music_url,
                'presentationVideoUrl': video_url,
                'appName': app_settings.app_name,
                'footerTagline': app_settings.footer_tagline,
                'socialLinks': app_settings.social_links or {},
            }
        })


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(
        tags=['Health'],
        summary='Health check endpoint',
        description=(
            'Check application health including database connectivity. '
            'No authentication required, no rate limiting.'
        ),
        responses={
            200: inline_serializer(
                name='HealthCheckResponse',
                fields={
                    'status': drf_serializers.CharField(),
                    'database': drf_serializers.CharField(),
                },
            ),
            503: inline_serializer(
                name='HealthCheckErrorResponse',
                fields={
                    'status': drf_serializers.CharField(),
                    'database': drf_serializers.CharField(),
                },
            ),
        },
        examples=[
            OpenApiExample(
                name='Healthy response',
                response_only=True,
                status_codes=['200'],
                value={'status': 'healthy', 'database': 'ok'},
            ),
            OpenApiExample(
                name='Unhealthy response',
                response_only=True,
                status_codes=['503'],
                value={'status': 'unhealthy', 'database': 'error'},
            ),
        ],
    )
    def get(self, request):
        try:
            # Test database connectivity with a simple query
            connection.ensure_connection()
            return Response(
                {'status': 'healthy', 'database': 'ok'},
                status=HTTP_200_OK,
            )
        except Exception:
            return Response(
                {'status': 'unhealthy', 'database': 'error'},
                status=HTTP_503_SERVICE_UNAVAILABLE,
            )
