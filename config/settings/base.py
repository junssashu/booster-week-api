import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.programs',
    'apps.enrollments',
    'apps.progress',
    'apps.sessions',
    'apps.testimonies',
    'apps.content',
    'apps.admin_api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'booster_week'),
        'USER': os.getenv('DB_USER', 'booster_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'booster_pass_2026'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.CustomPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'apps.core.renderers.CustomJSONRenderer',
    ),
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/min',
        'user': '100/min',
        'auth': '10/15min',
        'forgot_password': '3/15min',
        'payment': '5/15min',
        'qcm': '20/15min',
        'testimony': '5/15min',
        'contact_submit': '5/hour',
    },
}

# SimpleJWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'SIGNING_KEY': os.getenv('JWT_SECRET_KEY', SECRET_KEY),
    'ALGORITHM': 'HS256',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'sub',
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# MoneyFusion payment gateway
MONEYFUSION_API_KEY = os.getenv('MONEYFUSION_API_KEY', '')
MONEYFUSION_WEBHOOK_SECRET = os.getenv('MONEYFUSION_WEBHOOK_SECRET', '')
MONEYFUSION_BASE_URL = os.getenv('MONEYFUSION_BASE_URL', 'https://api.moneyfusion.net')
MONEYFUSION_WEBHOOK_URL = os.getenv('MONEYFUSION_WEBHOOK_URL', 'https://boosterweekcenter.com/api/v1/payments/webhook')
MONEYFUSION_RETURN_URL = os.getenv('MONEYFUSION_RETURN_URL', 'https://boosterweekcenter.com/paiement/confirmation')
MONEYFUSION_DEV_MODE = os.getenv('MONEYFUSION_DEV_MODE', 'True').lower() == 'true'

# MinIO / S3-compatible storage
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'storage.bibliothequessolidaires.org')
MINIO_PORT = int(os.environ.get('MINIO_PORT', '443'))
MINIO_USE_SSL = os.environ.get('MINIO_USE_SSL', 'true').lower() == 'true'
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', '')
MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', '')
MINIO_AUDIO_BUCKET = os.environ.get('MINIO_AUDIO_BUCKET', 'audios')
MINIO_DOCUMENT_BUCKET = os.environ.get('MINIO_DOCUMENT_BUCKET', 'documents')

# App config
BACKGROUND_MUSIC_URL = os.getenv(
    'BACKGROUND_MUSIC_URL',
    'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3',
)

# drf-spectacular (OpenAPI / Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Booster Week API',
    'DESCRIPTION': (
        'API backend pour l\'application Booster Week — programmes de formation, '
        'inscriptions, paiements MoneyFusion, progression, sessions live/replay, '
        'témoignages et contenu (FAQ / Contact).'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/v1/',
    'TAGS': [
        {'name': 'Config', 'description': 'Configuration publique de l\'application'},
        {'name': 'Auth', 'description': 'Inscription, connexion, tokens JWT, mot de passe'},
        {'name': 'Users', 'description': 'Profil utilisateur'},
        {'name': 'Programs', 'description': 'Programmes, degrés, étapes, assets'},
        {'name': 'Enrollments', 'description': 'Inscriptions aux programmes'},
        {'name': 'Payments', 'description': 'Paiements MoneyFusion (initiation, webhook, statut)'},
        {'name': 'Progress', 'description': 'Progression utilisateur (assets, QCM, formulaires, consignes)'},
        {'name': 'Sessions', 'description': 'Sessions live et replays'},
        {'name': 'Testimonies', 'description': 'Témoignages, likes, cœurs, commentaires'},
        {'name': 'Content', 'description': 'FAQ et informations de contact'},
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'ENUM_NAME_OVERRIDES': {},
}
