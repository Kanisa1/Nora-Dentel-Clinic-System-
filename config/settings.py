import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY','change-me-in-production')
DEBUG = os.getenv('DJANGO_DEBUG','False') == 'True'

# ALLOWED_HOSTS from environment variable
ALLOWED_HOSTS_ENV = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(',')]

# CSRF Settings
CSRF_TRUSTED_ORIGINS_ENV = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:8000,http://localhost:8000')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS_ENV.split(',')]

# CSRF Cookie settings
CSRF_COOKIE_SECURE = not DEBUG  # True in production with HTTPS
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access if needed
CSRF_COOKIE_SAMESITE = 'Lax'  # Prevent CSRF attacks
CSRF_USE_SESSIONS = False  # Use cookies instead of sessions for CSRF token

# Security Settings for Production
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Set to True when using HTTPS
    SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'clinic',
    'pharmacy',
    'inventory',
    'reports',
    'reception',
    'doctor',
    'tariff',
    'cashier',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For serving static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'clinic.context_processors.admin_stats',
        ],
    },
}]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB','nora_clinic_db'),
        'USER': os.getenv('POSTGRES_USER','nora_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD','nora_pass'),
        'HOST': os.getenv('POSTGRES_HOST','localhost'),
        'PORT': os.getenv('POSTGRES_PORT','5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Kigali'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration for serving static files
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AFRICASTALKING_USERNAME = "sandbox"
AFRICASTALKING_API_KEY = "atsk_ff8851e3abbb40564545a83e088774b66255425e782aea45cf84e1f5a9c4f89f47e4bdcf"

# CRONJOBS configuration
# Note: django_crontab is not compatible with Windows (requires 'fcntl' module)
# For scheduled tasks on Windows, use one of these alternatives:
# 1. Celery + Celery Beat (requires Redis/RabbitMQ)
# 2. APScheduler (lightweight, no message broker needed)
# 3. Windows Task Scheduler (built-in)

# Example scheduled tasks (commented out until task scheduler is configured):
# SCHEDULED_TASKS = [
#     # Every day at 09:00 (reminders)
#     ('0 9 * * *', 'clinic.cron.appointment_reminder'),
#     # Every day at 08:00 (birthdays)
#     ('0 8 * * *', 'clinic.cron.birthday_wishes'),
#     # Run at midnight daily (checks holidays)
#     ('0 0 * * *', 'clinic.cron.holiday_wishes'),
# ]


CLINIC_INFO = {
    "name": "Norha Dental Clinic",
    "address": "Kigali, Gasabo",
    "email": "norhadentalclinic@gmail.com",
    "phone": "+250798287919",
}

# Email Configuration for Development
# Use console backend to print emails to console instead of sending
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'noreply@noradentalclinic.com'

# --- Authentication Settings ---
# The default URL to redirect to after a successful login.
# This points to a view that will determine the user's role and redirect accordingly.
LOGIN_REDIRECT_URL = '/accounts/profile/'

# The URL where the default login page is located.
LOGIN_URL = '/auth/login/'

# The URL to redirect to after a user logs out.
LOGOUT_REDIRECT_URL = '/'

# Custom login URLs for specific roles, used by decorators.
RECEPTION_LOGIN_URL = '/reception/login/'
DOCTOR_LOGIN_URL = '/doctor/login/'
ADMIN_LOGIN_URL = '/admin/login/'
# --- End Authentication Settings ---


# Suppress WhatsApp sandbox warning
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="africastalking.Whatsapp")

