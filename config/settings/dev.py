from .base import *  # noqa: F401, F403

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True

# Relax throttling in dev
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/min',
    'user': '1000/min',
    'auth': '1000/15min',
    'forgot_password': '1000/15min',
    'payment': '1000/15min',
    'qcm': '1000/15min',
    'testimony': '1000/15min',
}
