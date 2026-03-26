"""
Django settings for myProject project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-17*1lk*o+6za%iia)y7_2#cw7wrw*8z8tn5ljq1vu63a!r-8uy'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',   # NEW — allows HTML frontend to call the API
    'myApp',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # NEW — must be at the top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],           # APP_DIRS=True already finds templates/myApp/ automatically
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'myApp.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'myProject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'

# Media files (uploaded product images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Where Django redirects after login/logout
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'


# ─────────────────────────────────────────────────────────────────
#  CORS — allow HTML frontend to call the Django API
#  Run:  pip install django-cors-headers
# ─────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS  = True      # OK for development/demo
CORS_ALLOW_CREDENTIALS  = True      # needed for session-based auth (login)


# ─────────────────────────────────────────────────────────────────
#  eSewa Sandbox Settings
#  Docs:  https://developer.esewa.com.np
#  These are the official eSewa sandbox/test credentials
# ─────────────────────────────────────────────────────────────────
ESEWA_MERCHANT_ID  = 'EPAYTEST'
ESEWA_SECRET_KEY   = '8gBm/:&EnhH.1/q'
ESEWA_PAYMENT_URL  = 'https://rc-epay.esewa.com.np/api/epay/main/v2/form'
ESEWA_SUCCESS_URL  = 'http://localhost:8000/api/payment/esewa/verify/'
ESEWA_FAILURE_URL  = 'http://localhost:8000/payment-failed/'


# ─────────────────────────────────────────────────────────────────
#  Khalti Sandbox Settings
#  Docs:  https://docs.khalti.com/khalti-epayment
#  These are the official Khalti sandbox/test credentials
# ─────────────────────────────────────────────────────────────────
KHALTI_SECRET_KEY   = 'test_secret_key_dc74e0fd57cb46cd93832aee0a390234'
KHALTI_INITIATE_URL = 'https://a.khalti.com/api/v2/epayment/initiate/'
KHALTI_LOOKUP_URL   = 'https://a.khalti.com/api/v2/epayment/lookup/'
KHALTI_RETURN_URL   = 'http://localhost:8000/api/payment/khalti/verify/'
KHALTI_WEBSITE_URL  = 'http://localhost:8000'

# ── Email (Gmail) ─────────────────────────────────────────────
# Email Configuration (SMTP)

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'martalpha2026@gmail.com'
EMAIL_HOST_PASSWORD = 'dfud ccgc zctc jmlj'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER