"""
Django settings for ProofVoice platform.
Supports MySQL database, DRF token authentication, multi-institution tenancy,
Gnani AI voice services, and CORS frontend integration.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Add apps directory to sys.path
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'apps'))

# Load environment variables from .env if present
load_dotenv(BASE_DIR / '.env')

# Security Settings
if os.getenv('DJANGO_DEBUG') is not None:
    DEBUG = os.getenv('DJANGO_DEBUG').strip().lower() in ('true', '1', 'yes')
elif os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_STATIC_URL') or os.getenv('ENVIRONMENT') == 'production':
    DEBUG = False
else:
    DEBUG = True

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-proofvoice-dev-fallback-key-2026'
    else:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured in environment when DEBUG=False.")

ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,testserver,.railway.app,.up.railway.app').split(',') if h.strip()]
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

# Security & Cookie Protection
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 'yes')
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', 31536000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    X_FRAME_OPTIONS = 'SAMEORIGIN'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party libraries
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

    # ProofVoice Core Applications
    'apps.accounts',
    'apps.institutions',
    'apps.complaints',
    'apps.notifications',
    'apps.integrations',
    'apps.analytics',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
        'DIRS': [BASE_DIR / 'templates'],
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
ASGI_APPLICATION = 'config.asgi.application'

# Database Configuration
# MySQL is the primary database for local development and production.
# SQLite is only activated during automated test suites if USE_SQLITE_FOR_TESTS is explicitly enabled.
USE_SQLITE_FOR_TESTS = os.getenv('USE_SQLITE_FOR_TESTS', 'False').lower() in ('true', '1', 'yes')
IS_RUNNING_TESTS = 'test' in sys.argv or 'makemigrations' in sys.argv or 'seed_demo_data' in sys.argv or 'migrate' in sys.argv or 'reset_user_password' in sys.argv

if USE_SQLITE_FOR_TESTS or ('test' in sys.argv):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_proofvoice.sqlite3',
        }
    }
else:
    DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.mysql')
    DB_NAME = os.getenv('DB_NAME', os.getenv('MYSQLDATABASE', 'proofvoice_db'))
    DB_USER = os.getenv('DB_USER', os.getenv('MYSQLUSER', 'proofvoice_user'))
    DB_PASSWORD = os.getenv('DB_PASSWORD', os.getenv('MYSQLPASSWORD'))
    DB_HOST = os.getenv('DB_HOST', os.getenv('MYSQLHOST', '127.0.0.1'))
    DB_PORT = os.getenv('DB_PORT', os.getenv('MYSQLPORT', '3306'))

    if DB_PASSWORD is None:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            "DB_PASSWORD is missing in backend/.env. "
            "Please configure MySQL credentials before starting Django."
        )

    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', 60)),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise production compressed static file storage
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media Files (Attachments & Logos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 5))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# In-Memory Cache Configuration for Throttling & Brute-Force Defense
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'proofvoice-security-cache',
    }
}

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.accounts.authentication.ExpiringTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '120/min',
        'user': '300/min',
        'login': '5/min',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
    'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
}

# Cross-Origin Resource Sharing (CORS) & CSRF Configuration
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# Strict Origin Whitelist
DEV_CORS_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:5500',
    'http://127.0.0.1:5500',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]

PROD_CORS_ORIGINS = [
    'https://proofvoice.vercel.app',
]

custom_origin_env = os.getenv('FRONTEND_ORIGIN', '').strip()
if custom_origin_env:
    for single_origin in custom_origin_env.split(','):
        clean_origin = single_origin.strip()
        if clean_origin and clean_origin not in PROD_CORS_ORIGINS:
            PROD_CORS_ORIGINS.append(clean_origin)

if DEBUG:
    CORS_ALLOWED_ORIGINS = sorted(list(set(DEV_CORS_ORIGINS + PROD_CORS_ORIGINS)))
else:
    CORS_ALLOWED_ORIGINS = sorted(list(set(PROD_CORS_ORIGINS)))

# Removed broad Vercel subdomain regex - exact production origins only
CORS_ALLOWED_ORIGIN_REGEXES = []

CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)
railway_static = os.getenv('RAILWAY_STATIC_URL', '').strip()
if railway_static and railway_static not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(railway_static)

# Gnani AI Service Settings (https://docs.gnani.ai/)
GNANI_API_KEY = os.getenv('GNANI_API_KEY', '')
GNANI_API_BASE_URL = os.getenv('GNANI_API_BASE_URL', 'https://api.vachana.ai').rstrip('/')
GNANI_STT_ENDPOINT = f"{GNANI_API_BASE_URL}/stt/v3"
GNANI_TTS_ENDPOINT = f"{GNANI_API_BASE_URL}/api/v1/tts/inference"

# OpenAI Conversational AI Reasoning Settings (https://platform.openai.com/)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini').strip()
OPENAI_API_BASE_URL = os.getenv('OPENAI_API_BASE_URL', 'https://api.openai.com/v1').strip().rstrip('/')

# Google Gemini API Settings (Secondary LLM Reasoning)
GEMINI_API_KEY = (os.getenv('GEMINI_API_KEY', '') or os.getenv('GOOGLE_API_KEY', '')).strip()

# In-App Notification Mode - No External Email Delivery Services
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
DEFAULT_FROM_EMAIL = 'ProofVoice Platform <notifications@proofvoice.platform>'
SUPER_ADMIN_ROLE = 'PLATFORM_SUPERADMIN'

