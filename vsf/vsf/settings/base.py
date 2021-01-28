"""
Django settings for vsf project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import environ

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys

PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# Vars that sets the environment settings

env = environ.Env()
environ.Env.read_env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('VSF_SECRET_KEY')

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
]


INSTALLED_APPS = [
    'apps.vsf_base.apps.VsfBaseConfig',
    'apps.configs.apps.ConfigsConfig',
    'apps.main.events.apps.EventsConfig',
    'apps.main.cases.apps.CasesConfig',
    'apps.main.measurements.flags.apps.FlagsConfig',
    'apps.main.measurements.apps.MeasurementsConfig',
    'apps.main.measurements.submeasurements.apps.SubmeasurementsConfig',
    'apps.main.ooni_fp.fp_tables.apps.FpTablesConfig',
    'apps.main.sites.apps.SitesConfig',
    'apps.main.asns.apps.AsnsConfig',
    'apps.dashboard.apps.DashboardConfig',
]

API_APPS = [
    'apps.api.asns_api.apps.AsnsAPIConfig',
    'apps.api.fp_tables_api.apps.FpTablesAPIConfig',
    'apps.api.cases_api.apps.CasesAPIConfig',
    'apps.api.events_api.apps.EventsAPIConfig',
    'apps.api.measurements_api.apps.MeasurementsAPIConfig',

]

THIRD_PARTY_APPS = [
    'widget_tweaks',
    'drf_yasg',
    'django_celery_results',
    'django_celery_beat',
    'django_sass',
]


INSTALLED_APPS = INSTALLED_APPS + DJANGO_APPS + API_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vsf.urls'

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

WSGI_APPLICATION = 'vsf.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env.str('VSF_DB_NAME'),
        'USER': env.str('VSF_DB_USER'),
        'PASSWORD': env.str('VSF_DB_PASSWORD'),
        'HOST': env.str('VSF_DB_HOST'),
        'PORT': env.str('VSF_DB_PORT')
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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

# Authentication
# --------------------------------------------------

LOGIN_URL = "/dashboard/login"

LOGIN_REDIRECT_URL = "/dashboard"

LOGOUT_REDIRECT_URL = LOGIN_URL

# EMAIL
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# FOR DEBUG ONLY
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "sent_emails")

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
     os.path.join(BASE_DIR, 'vsf', 'static'),
)

STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static')

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND  = 'django-cache'

# Caching config:
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'process_state',
        'TIMEOUT' : 86400
    }
}