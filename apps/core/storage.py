"""
MinIO/S3 storage utility for resolving asset URLs.

Convention for external_url field:
- If starts with 'http://' or 'https://' -> external URL, return as-is
- If starts with 'minio://' -> MinIO object, build direct public URL
  Format: minio://bucket/key (e.g., minio://documents/guide.pdf)
"""
import unicodedata
from urllib.parse import quote

from django.conf import settings


def resolve_url(external_url: str, expiry: int = 3600) -> str:
    """
    Resolve an external_url to a downloadable URL.

    - Regular URLs (http/https) are returned as-is
    - MinIO references (minio://bucket/key) get a direct public URL
      (buckets are configured with public download access)
    """
    if not external_url:
        return external_url

    if external_url.startswith('minio://'):
        # Parse minio://bucket/key
        path = external_url[len('minio://'):]
        parts = path.split('/', 1)
        if len(parts) != 2:
            return external_url  # malformed, return as-is
        bucket, key = parts
        # Normalize key to NFD — files uploaded from macOS use decomposed Unicode
        key = unicodedata.normalize('NFD', key)
        # URL-encode the key path segments (preserve /)
        encoded_key = quote(key, safe='/')
        # Build direct public URL
        protocol = 'https' if settings.MINIO_USE_SSL else 'http'
        base_url = f"{protocol}://{settings.MINIO_ENDPOINT}"
        if settings.MINIO_PORT not in (80, 443):
            base_url = f"{base_url}:{settings.MINIO_PORT}"
        return f"{base_url}/{bucket}/{encoded_key}"

    # Regular URL - return as-is
    return external_url


def get_bucket_for_type(asset_type: str) -> str:
    """Return the MinIO bucket name for a given asset type."""
    if asset_type in {'audio'}:
        return settings.MINIO_AUDIO_BUCKET
    return settings.MINIO_DOCUMENT_BUCKET


def build_minio_url(bucket: str, key: str) -> str:
    """Build a minio:// URL for storage in the database."""
    return f"minio://{bucket}/{key}"
