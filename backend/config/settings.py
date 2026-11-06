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

# Load environment variables from .env if present (local development only)
# Railway production injects configuration directly via Railway Service Variables.
if not os.getenv('RAILWAY_ENVIRONMENT'):
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
IS_RUNNING_TESTS = 'test' in sys.argv

if USE_SQLITE_FOR_TESTS or ('test' in sys.argv):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_proofvoice.sqlite3',
        }
    }
else:
    from urllib.parse import urlparse, unquote

    def _clean_db_env(val):
        """Safely cleans an environment variable: strips whitespace, tabs, newlines, and wrapping quotes."""
        if val is None:
            return None, False
        raw_val = str(val)
        cleaned = raw_val.strip()
        if len(cleaned) >= 2 and ((cleaned[0] == '"' and cleaned[-1] == '"') or (cleaned[0] == "'" and cleaned[-1] == "'")):
            cleaned = cleaned[1:-1].strip()
        was_stripped = (cleaned != raw_val)
        if cleaned == '':
            return None, was_stripped
        return cleaned, was_stripped

    # Detect Railway production environment
    IS_RAILWAY_PROD = (
        bool(os.getenv('RAILWAY_ENVIRONMENT')) or 
        bool(os.getenv('RAILWAY_STATIC_URL')) or 
        bool(os.getenv('RAILWAY_PROJECT_ID')) or 
        bool(os.getenv('RAILWAY_SERVICE_ID')) or
        bool(os.getenv('MYSQLHOST'))
    )
    IS_PRODUCTION = (not DEBUG) or IS_RAILWAY_PROD or (os.getenv('ENVIRONMENT', '').strip().lower() == 'production')

    # Optional URL connection string parsing (MYSQL_URL / DATABASE_URL)
    raw_db_url, _ = _clean_db_env(os.getenv('MYSQL_URL') or os.getenv('DATABASE_URL'))
    url_params = {}
    if raw_db_url and raw_db_url.startswith(('mysql://', 'mysqlclient://')):
        try:
            parsed_url = urlparse(raw_db_url)
            if parsed_url.hostname:
                url_params['host'] = unquote(parsed_url.hostname).strip()
            if parsed_url.port:
                url_params['port'] = str(parsed_url.port).strip()
            if parsed_url.username:
                url_params['user'] = unquote(parsed_url.username).strip()
            if parsed_url.password:
                url_params['password'] = unquote(parsed_url.password).strip()
            if parsed_url.path and len(parsed_url.path) > 1:
                url_params['name'] = unquote(parsed_url.path.lstrip('/')).strip()
        except Exception:
            pass

    stripped_vars = []

    used_url_params = []

    def _get_db_var(primary_key, fallback_key=None, default=None, param_name=None):
        # When Railway MYSQL* variables exist (or on Railway platform), they strictly take priority
        # over any DB_* variables, even if DB_HOST or DB_USER contains an incorrect non-localhost address
        has_railway_val = fallback_key and bool(os.getenv(fallback_key))
        if (IS_RAILWAY_PROD or has_railway_val) and has_railway_val:
            raw = os.getenv(fallback_key)
            src = fallback_key
        else:
            raw = os.getenv(primary_key)
            src = primary_key
            if raw is None and fallback_key:
                raw = os.getenv(fallback_key)
                src = fallback_key

        cleaned, stripped = _clean_db_env(raw)
        if stripped and src:
            stripped_vars.append(src)

        if cleaned is not None:
            return cleaned

        if default is not None:
            if param_name and (raw_db_url and default == url_params.get(param_name)):
                used_url_params.append(param_name)
            return default

        return None

    DB_ENGINE = _get_db_var('DB_ENGINE', default='django.db.backends.mysql')

    # Host: DB_HOST -> MYSQLHOST -> URL host -> (127.0.0.1 only in local dev; NEVER hardcoded in production)
    DB_HOST = _get_db_var('DB_HOST', 'MYSQLHOST', default=url_params.get('host'), param_name='host')
    if not DB_HOST and not IS_PRODUCTION:
        DB_HOST = '127.0.0.1'

    # Port: DB_PORT -> MYSQLPORT -> URL port -> 3306
    DB_PORT = _get_db_var('DB_PORT', 'MYSQLPORT', default=url_params.get('port') or '3306', param_name='port')

    # Database Name: DB_NAME -> MYSQLDATABASE -> URL name -> proofvoice_db
    DB_NAME = _get_db_var('DB_NAME', 'MYSQLDATABASE', default=url_params.get('name') or 'proofvoice_db', param_name='name')

    # User: DB_USER -> MYSQLUSER -> URL user -> (proofvoice_user only in local dev; NO hardcoded root in production)
    DB_USER = _get_db_var('DB_USER', 'MYSQLUSER', default=url_params.get('user'), param_name='user')
    if not DB_USER and not IS_PRODUCTION:
        DB_USER = 'proofvoice_user'

    # Password: DB_PASSWORD -> MYSQLPASSWORD -> URL password
    DB_PASSWORD = _get_db_var('DB_PASSWORD', 'MYSQLPASSWORD', default=url_params.get('password'), param_name='password')

    # Connection Max Age: DB_CONN_MAX_AGE -> 60
    conn_age_raw, _ = _clean_db_env(os.getenv('DB_CONN_MAX_AGE', '60'))
    try:
        DB_CONN_MAX_AGE = int(conn_age_raw) if conn_age_raw else 60
    except (ValueError, TypeError):
        DB_CONN_MAX_AGE = 60

    # Validation and error reporting
    missing_configs = []
    if not DB_HOST:
        missing_configs.append("DB_HOST (or MYSQLHOST) is missing. In production, set MYSQLHOST to your Railway MySQL private host (e.g., mysql.railway.internal).")
    elif IS_RAILWAY_PROD and DB_HOST.lower() in ('127.0.0.1', 'localhost', '::1'):
        missing_configs.append(f"DB_HOST / MYSQLHOST is set to '{DB_HOST}' on Railway. A production Railway deployment cannot connect to localhost; set MYSQLHOST to your Railway MySQL host (e.g., mysql.railway.internal).")

    if not DB_USER:
        missing_configs.append("DB_USER (or MYSQLUSER) is missing.")

    if not DB_NAME:
        missing_configs.append("DB_NAME (or MYSQLDATABASE) is missing.")

    if not DB_PASSWORD:
        missing_configs.append("DB_PASSWORD (or MYSQLPASSWORD) is missing.")

    if DB_PORT:
        try:
            p_int = int(DB_PORT)
            if p_int <= 0 or p_int > 65535:
                missing_configs.append(f"DB_PORT / MYSQLPORT is outside valid port range: '{DB_PORT}'")
        except ValueError:
            missing_configs.append(f"DB_PORT / MYSQLPORT is not a valid integer: '{DB_PORT}'")

    if missing_configs:
        from django.core.exceptions import ImproperlyConfigured
        bullet_list = "\n  - ".join(missing_configs)
        raise ImproperlyConfigured(
            f"\n[ProofVoice Database Configuration Error]\n"
            f"The following required database settings are missing or malformed:\n"
            f"  - {bullet_list}\n"
            f"\nPlease configure these in your Railway Project Service Variables "
            f"(or backend/.env for local development), or provide a valid MYSQL_URL / DATABASE_URL connection string."
        )

    # Safe diagnostic logging (never prints passwords or secrets)
    import logging
    db_logger = logging.getLogger('proofvoice.database')
    env_label = "Railway Production" if IS_PRODUCTION else "Local Development"
    pwd_indicator = f"[SET - {len(DB_PASSWORD)} chars]" if DB_PASSWORD else "[MISSING]"
    diag_lines = [
        f"[ProofVoice DB Config] Mode: {env_label}",
        f"[ProofVoice DB Config] Engine: {DB_ENGINE}",
        f"[ProofVoice DB Config] Host: {DB_HOST}",
        f"[ProofVoice DB Config] Port: {DB_PORT}",
        f"[ProofVoice DB Config] Database: {DB_NAME}",
        f"[ProofVoice DB Config] User: {DB_USER}",
        f"[ProofVoice DB Config] Password: {pwd_indicator}",
        f"[ProofVoice DB Config] Connection Max Age: {DB_CONN_MAX_AGE}s",
    ]
    if stripped_vars:
        diag_lines.append(f"[ProofVoice DB Config] Sanitized (stripped whitespace/tabs/quotes): {', '.join(sorted(set(stripped_vars)))}")
    if used_url_params:
        diag_lines.append(f"[ProofVoice DB Config] Fallback Notice: Parameter(s) [{', '.join(sorted(set(used_url_params)))}] were populated from MYSQL_URL / DATABASE_URL fallback (no individual variable set).")

    for line in diag_lines:
        db_logger.info(line)

    # Print to stdout during migrations, runserver, or Railway startup for immediate log visibility
    if IS_RAILWAY_PROD or ('migrate' in sys.argv or 'runserver' in sys.argv):
        print("\n".join(diag_lines), flush=True)

    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'CONN_MAX_AGE': DB_CONN_MAX_AGE,
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
# Defaults to BASE_DIR / 'media' which aligns with the Railway persistent volume at /app/backend/media
MEDIA_URL = '/media/'
_CUSTOM_MEDIA_ROOT = os.getenv('MEDIA_ROOT', '').strip()
MEDIA_ROOT = Path(_CUSTOM_MEDIA_ROOT) if _CUSTOM_MEDIA_ROOT else (BASE_DIR / 'media')
MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 5))

# Safely initialize required media volume subdirectories
try:
    os.makedirs(MEDIA_ROOT / 'profile_photos', exist_ok=True)
    os.makedirs(MEDIA_ROOT / 'complaints' / 'attachments', exist_ok=True)
    os.makedirs(MEDIA_ROOT / 'institutions' / 'logos', exist_ok=True)
    os.makedirs(MEDIA_ROOT / 'institutions' / 'docs', exist_ok=True)
except Exception:
    pass

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

def _normalize_origin(origin_val, default_scheme='https'):
    """
    Normalizes an origin for CORS_ALLOWED_ORIGINS and CSRF_TRUSTED_ORIGINS.
    - Strips whitespace, tabs, newlines, and trailing slashes.
    - Strips accidental wrapping quotes.
    - If scheme (http:// or https://) is missing:
      - Prepends http:// for localhost / loopback addresses.
      - Prepends default_scheme (https://) for all production/cloud domains.
    - Never returns a bare hostname without a valid scheme.
    """
    if not origin_val:
        return None
    raw = str(origin_val).strip()
    if len(raw) >= 2 and ((raw[0] == '"' and raw[-1] == '"') or (raw[0] == "'" and raw[-1] == "'")):
        raw = raw[1:-1].strip()
    cleaned = raw.rstrip('/')
    if not cleaned:
        return None

    if cleaned.startswith(('http://', 'https://')):
        return cleaned

    # Prepend appropriate scheme
    if (
        cleaned.startswith(('localhost', '127.0.0.1', '0.0.0.0', '::1')) or 
        ':3000' in cleaned or ':5173' in cleaned or ':8000' in cleaned or ':8080' in cleaned
    ):
        return f"http://{cleaned}"
    return f"{default_scheme}://{cleaned}"

# Strict Local Development Origins
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

# Strict Production Origins (Vercel Frontend & Railway Backend)
PROD_FRONTEND_ORIGIN = 'https://proofvoice.vercel.app'
PROD_BACKEND_ORIGIN = 'https://web-production-39c80.up.railway.app'

PROD_CORS_ORIGINS = [
    PROD_FRONTEND_ORIGIN,
    PROD_BACKEND_ORIGIN,
]

# Process FRONTEND_ORIGIN / BACKEND_ORIGIN environment variables if provided
for env_key in ['FRONTEND_ORIGIN', 'BACKEND_ORIGIN']:
    env_val = os.getenv(env_key, '').strip()
    if env_val:
        for single in env_val.split(','):
            norm = _normalize_origin(single, default_scheme='https')
            if norm and norm not in PROD_CORS_ORIGINS:
                PROD_CORS_ORIGINS.append(norm)

# Final CORS_ALLOWED_ORIGINS list (scheme guaranteed, duplicates removed)
if DEBUG:
    raw_cors = DEV_CORS_ORIGINS + PROD_CORS_ORIGINS
else:
    raw_cors = PROD_CORS_ORIGINS

CORS_ALLOWED_ORIGINS = sorted(list(set(
    filter(None, [_normalize_origin(o, default_scheme='https') for o in raw_cors])
)))

# Removed broad Vercel subdomain regex - exact production origins only
CORS_ALLOWED_ORIGIN_REGEXES = []

# CSRF Trusted Origins - every origin must strictly include a scheme (http:// or https://)
csrf_candidates = list(CORS_ALLOWED_ORIGINS)

# Read environment variables that contribute to CSRF_TRUSTED_ORIGINS:
# - CSRF_TRUSTED_ORIGINS (manual env var, may be comma-separated or bare hostnames)
# - RAILWAY_STATIC_URL (Railway platform variable)
# - RAILWAY_PUBLIC_DOMAIN (Railway platform variable)
csrf_env = os.getenv('CSRF_TRUSTED_ORIGINS', '').strip()
if csrf_env:
    for single in csrf_env.split(','):
        norm = _normalize_origin(single, default_scheme='https')
        if norm:
            csrf_candidates.append(norm)

for railway_key in ['RAILWAY_STATIC_URL', 'RAILWAY_PUBLIC_DOMAIN']:
    r_val = os.getenv(railway_key, '').strip()
    if r_val:
        for single in r_val.split(','):
            norm = _normalize_origin(single, default_scheme='https')
            if norm:
                csrf_candidates.append(norm)

# Guarantee every entry in CSRF_TRUSTED_ORIGINS is normalized with a scheme and deduplicated
CSRF_TRUSTED_ORIGINS = sorted(list(set(
    filter(None, [_normalize_origin(o, default_scheme='https') for o in csrf_candidates])
)))

# Gnani AI Service Settings (https://docs.gnani.ai/)
GNANI_API_KEY = os.getenv('GNANI_API_KEY', '')
GNANI_API_BASE_URL = os.getenv('GNANI_API_BASE_URL', 'https://api.vachana.ai').rstrip('/')
GNANI_STT_ENDPOINT = f"{GNANI_API_BASE_URL}/stt/v3"
GNANI_TTS_ENDPOINT = f"{GNANI_API_BASE_URL}/api/v1/tts/inference"
GNANI_STT_MODEL = os.getenv('GNANI_STT_MODEL', 'prisma-v3.0')

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

