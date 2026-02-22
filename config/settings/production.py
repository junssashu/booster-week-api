import os
from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# CORS – allow the mobile app and specific origins
CORS_ALLOW_ALL_ORIGINS = True

# Security
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
