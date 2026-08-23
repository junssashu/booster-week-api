import logging
import os
import subprocess
import tempfile
import threading
from datetime import date

from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Enrollment
from .views_schemas import _MONTHS_FR

logger = logging.getLogger(__name__)


class AttestationView(APIView):
    """Generate and stream a personalised PDF attestation for a completed enrollment."""
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id):
        import io as _io
        from django.http import FileResponse
        from docxtpl import DocxTemplate
        from apps.progress.models import QCMAttempt
        from django.db.models import Max
        from minio import Minio

        try:
            enrollment = Enrollment.objects.select_related('user', 'program').get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return Response({'error': 'Inscription introuvable'}, status=404)

        if enrollment.user != request.user and not request.user.is_staff:
            return Response({'error': 'Accès interdit'}, status=403)

        if not enrollment.all_degrees_completed():
            return Response({'error': 'Programme non terminé'}, status=403)

        program = enrollment.program
        user = enrollment.user

        participant_name = f"{user.first_name} {user.last_name}".strip() or user.phone

        w = program.duration_weeks
        duration = f"{w // 4} mois" if w % 4 == 0 else f"{w} semaines"

        today = date.today()
        date_str = f"{today.day:02d} {_MONTHS_FR[today.month - 1]} {today.year}"
        year = str(today.year)

        scores_qs = (
            QCMAttempt.objects
            .filter(user=user, asset__step__degree__program=program)
            .values('asset_id')
            .annotate(best=Max('score'))
        )
        scores = list(scores_qs)
        if scores:
            avg = sum(float(s['best']) for s in scores) / len(scores)
            if avg >= 90:
                mention = "EXCELLENT"
            elif avg >= 80:
                mention = "TRÈS BIEN"
            else:
                mention = "BIEN"
        else:
            mention = "BIEN"

        if program.modules_text:
            modules = program.modules_text
        else:
            parts = []
            for degree in program.degrees.order_by('order_index').prefetch_related('steps'):
                step_titles = " - ".join(s.title for s in degree.steps.order_by('order_index'))
                parts.append(f"{degree.title} : {step_titles}" if step_titles else degree.title)
            modules = " | ".join(parts)

        template_path = os.path.join(
            settings.BASE_DIR, 'apps', 'content', 'attestation_template_FINAL.docx'
        )
        tpl = DocxTemplate(template_path)
        tpl.render({
            'participant_name': participant_name,
            'program_name': program.name,
            'duration': duration,
            'year': year,
            'date': date_str,
            'mention': mention,
            'modules': modules,
        })

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False, dir='/tmp') as f:
            docx_path = f.name
        tpl.save(docx_path)

        subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', '/tmp', docx_path],
            check=True, capture_output=True, timeout=60,
        )
        pdf_path = docx_path.replace('.docx', '.pdf')

        try:
            pdf_bytes = open(pdf_path, 'rb').read()
            minio_endpoint = (
                f"{settings.MINIO_ENDPOINT}:{settings.MINIO_PORT}"
                if settings.MINIO_PORT not in (80, 443) else settings.MINIO_ENDPOINT
            )
            minio_client = Minio(
                minio_endpoint,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_USE_SSL,
            )
            minio_key = f"attestations/{enrollment_id}.pdf"
            minio_client.put_object(
                settings.MINIO_DOCUMENT_BUCKET, minio_key,
                _io.BytesIO(pdf_bytes), length=len(pdf_bytes), content_type='application/pdf',
            )
            logger.info("Attestation uploaded to MinIO: %s/%s", settings.MINIO_DOCUMENT_BUCKET, minio_key)
        except Exception as exc:
            logger.warning("MinIO upload failed for attestation %s: %s", enrollment_id, exc)

        def _cleanup():
            import time
            time.sleep(10)
            for p in (docx_path, pdf_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass

        threading.Thread(target=_cleanup, daemon=True).start()

        safe_name = enrollment_id.replace('/', '_')
        return FileResponse(
            open(pdf_path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"attestation_{safe_name}.pdf",
        )
