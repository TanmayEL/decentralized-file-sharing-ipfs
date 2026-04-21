import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('DJANGO_SECRET_KEY environment variable is not set')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']

# no Django ORM — we talk to MongoDB directly via pymongo
INSTALLED_APPS = [
    'corsheaders',
    'rest_framework',
    'auth_app',
    'files_app',
    'admin_app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'ipfs_backend.urls'
WSGI_APPLICATION = 'ipfs_backend.wsgi.application'

# no SQL database — pymongo handles MongoDB
DATABASES = {}

# CORS — allow the frontend
_frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
_extra_origins = [o.strip() for o in os.environ.get('CORS_EXTRA_ORIGINS', '').split(',') if o.strip()]
CORS_ALLOWED_ORIGINS = [_frontend_url] + _extra_origins
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'anon': '100/15min'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

_upload_limit_mb = int(os.environ.get('UPLOAD_LIMIT_MB', 10))
DATA_UPLOAD_MAX_MEMORY_SIZE = _upload_limit_mb * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = _upload_limit_mb * 1024 * 1024
