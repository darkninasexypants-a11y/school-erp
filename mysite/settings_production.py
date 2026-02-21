"""
Django settings for mysite project.
Production-ready settings for PythonAnywhere deployment.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SECURITY SETTINGS
# ============================================================
# SECRET_KEY: PythonAnywhere ke environment variable se aayega
# Ya neeche directly likh sakte ho (sirf PythonAnywhere ke liye)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-this-to-a-random-secret-key-in-production')

# PythonAnywhere par DEBUG = False karo
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# PythonAnywhere ka domain add karo
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.pythonanywhere.com',   # ← PythonAnywhere ka domain
]

# CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://*.pythonanywhere.com',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_NAME = 'csrftoken'


# ============================================================
# INSTALLED APPS
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'students_app',
    'ai_question_generator',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'students_app.context_processors.current_school',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'


# ============================================================
# DATABASE - PythonAnywhere MySQL
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'school_erp_db'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC & MEDIA FILES
# ============================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # collectstatic yahan save karega

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# AUTHENTICATION
# ============================================================
AUTHENTICATION_BACKENDS = [
    'students_app.authentication.MultiUserAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/admin-dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

ADMIN_URL = 'super-admin/'


# ============================================================
# ENCRYPTION KEY
# ============================================================
try:
    COMMUNICATION_ENCRYPTION_KEY = os.environ.get('COMMUNICATION_ENCRYPTION_KEY')
    if not COMMUNICATION_ENCRYPTION_KEY:
        from cryptography.fernet import Fernet
        COMMUNICATION_ENCRYPTION_KEY = Fernet.generate_key().decode()
except ImportError:
    COMMUNICATION_ENCRYPTION_KEY = None


# ============================================================
# REST FRAMEWORK
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'students_app.pagination.CustomPageNumberPagination',
    'PAGE_SIZE': 20,
}


# ============================================================
# CORS
# ============================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:19006",
]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization',
    'content-type', 'dnt', 'origin', 'user-agent',
    'x-csrftoken', 'x-requested-with',
]


# ============================================================
# EMAIL (Development: console, Production: SMTP)
# ============================================================
DEFAULT_FROM_EMAIL = 'noreply@schoolerp.com'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ============================================================
# RAZORPAY (optional)
# ============================================================
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')


# ============================================================
# TWILIO (optional)
# ============================================================
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
