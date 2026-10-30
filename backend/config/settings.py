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
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-proofvoice-dev-fallback-key-2026'
    else:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured in environment when DEBUG=False.")

ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,testserver').split(',') if h.strip()]
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

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

if IS_RUNNING_TESTS and USE_SQLITE_FOR_TESTS:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_proofvoice.sqlite3',
        }
    }
else:
    DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.mysql')
    DB_NAME = os.getenv('DB_NAME', 'proofvoice_db')
    DB_USER = os.getenv('DB_USER', 'proofvoice_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = os.getenv('DB_PORT', '3306')

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

# Media Files (Attachments & Logos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 5))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',
}

# Cross-Origin Resource Sharing (CORS)
CORS_ALLOW_CREDENTIALS = True
cors_origins_env = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173')
CORS_ALLOWED_ORIGINS = [orig.strip() for orig in cors_origins_env.split(',') if orig.strip()]
CORS_ALLOW_ALL_ORIGINS = False
CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)

# Gnani AI Service Settings (https://docs.gnani.ai/)
GNANI_API_KEY = os.getenv('GNANI_API_KEY', '')
GNANI_API_BASE_URL = os.getenv('GNANI_API_BASE_URL', 'https://api.vachana.ai').rstrip('/')
GNANI_STT_ENDPOINT = f"{GNANI_API_BASE_URL}/stt/v3"
GNANI_TTS_ENDPOINT = f"{GNANI_API_BASE_URL}/api/v1/tts/inference"
