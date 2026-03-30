from pathlib import Path
import os
from urllib.parse import urlparse
import dj_database_url
from dotenv import load_dotenv
try:
    import certifi
except Exception:
    certifi = None


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}

DEBUG = env_bool('DEBUG', True)
SECRET_KEY = os.getenv('SECRET_KEY') or ('dev-only-change-me' if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY environment variable is required when DEBUG=0')


def env_list(name, default=''):
    value = os.getenv(name)
    if value is None:
        value = default
    if isinstance(value, list):
        return [item.strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(',') if item.strip()]


def normalize_host(host):
    host = str(host or '').strip()
    if not host:
        return ''
    if '://' in host:
        parsed = urlparse(host)
        return parsed.hostname or ''
    return host.split('/')[0].strip()


def normalize_origin(origin):
    origin = str(origin or '').strip()
    if not origin:
        return ''
    if '://' not in origin:
        origin = f'https://{origin}'
    parsed = urlparse(origin)
    if not parsed.scheme or not parsed.netloc:
        return ''
    return f'{parsed.scheme}://{parsed.netloc}'


raw_allowed_hosts = env_list('ALLOWED_HOSTS', ['localhost', '127.0.0.1'] if DEBUG else [])
ALLOWED_HOSTS = [host for host in (normalize_host(item) for item in raw_allowed_hosts) if host]

raw_csrf_trusted_origins = env_list(
    'CSRF_TRUSTED_ORIGINS',
    ['http://localhost', 'http://127.0.0.1'] if DEBUG else [],
)
CSRF_TRUSTED_ORIGINS = [
    origin for origin in (normalize_origin(item) for item in raw_csrf_trusted_origins) if origin
]

render_hostname = normalize_host(os.getenv('RENDER_EXTERNAL_HOSTNAME', ''))
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)
if render_hostname:
    render_origin = normalize_origin(render_hostname)
    if render_origin and render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)
if not DEBUG and not ALLOWED_HOSTS:
    raise RuntimeError('ALLOWED_HOSTS must be configured when DEBUG=0')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'accounts',
    'shayari',
    'translation',
    'moderation',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lafzloom.urls'

JINJA2_DIRS = [
    BASE_DIR / 'templates',
    BASE_DIR / 'accounts' / 'templates',
    BASE_DIR / 'shayari' / 'templates',
    BASE_DIR / 'moderation' / 'templates',
]
DJANGO_TEMPLATE_DIRS = [
    BASE_DIR / 'django_templates',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': JINJA2_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'lafzloom.jinja2.environment',
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'lafzloom.context_processors.csrf_input',
            ],
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': DJANGO_TEMPLATE_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'lafzloom.context_processors.csrf_input',
            ],
        },
    },
]

WSGI_APPLICATION = 'lafzloom.wsgi.application'
ASGI_APPLICATION = 'lafzloom.asgi.application'

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'lafzloom'),
            'USER': os.getenv('POSTGRES_USER', 'lafzloom'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'lafzloom'),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }

EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_ALLOW_INSECURE_TLS = env_bool('EMAIL_ALLOW_INSECURE_TLS', False)
if DEBUG and EMAIL_ALLOW_INSECURE_TLS and EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_BACKEND = 'lafzloom.email_backend.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', False)
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '15'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '').replace(' ', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@lafzloom.com')
EMAIL_SSL_CERTFILE = os.getenv('EMAIL_SSL_CERTFILE') or None
if not EMAIL_SSL_CERTFILE and certifi:
    EMAIL_SSL_CERTFILE = certifi.where()

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'en')
LANGUAGES = [
    ('en', 'English'),
    ('hi', 'Hindi'),
    ('ur', 'Urdu'),
]
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', not DEBUG)
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', not DEBUG)
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000' if not DEBUG else '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', not DEBUG)
SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = env_bool('SECURE_CONTENT_TYPE_NOSNIFF', not DEBUG)
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY')

TRANSLATION_PROVIDER = os.getenv('TRANSLATION_PROVIDER', 'mock')
TRANSLATION_TIMEOUT_SECONDS = int(os.getenv('TRANSLATION_TIMEOUT_SECONDS', '20'))
