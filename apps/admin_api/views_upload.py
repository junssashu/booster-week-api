import io
import uuid

from django.conf import settings
from minio import Minio
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminOrAssistant
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
    permission_classes = [IsAdminOrAssistant]
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

        content_type = file.content_type
        allowed = [t for types in self.ALLOWED_TYPES.values() for t in types]
        if content_type not in allowed:
            return Response({'error': f'File type {content_type} not allowed'}, status=400)

        try:
            client = _get_minio_client()
            ext = file.name.rsplit('.', 1)[-1] if '.' in file.name else ''
            filename = f"{uuid.uuid4().hex[:12]}.{ext}" if ext else uuid.uuid4().hex[:12]
            object_name = f"{folder}/{filename}" if folder else filename
            file_data = file.read()
            client.put_object(
                bucket, object_name, io.BytesIO(file_data),
                length=len(file_data), content_type=content_type,
            )
            minio_ref = f"minio://{bucket}/{object_name}"
            url = resolve_url(minio_ref)
            return Response({'data': {'url': url, 'filename': filename}})
        except Exception as e:
            return Response({'error': f'Upload failed: {str(e)}'}, status=500)
