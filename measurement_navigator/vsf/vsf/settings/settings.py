from .base import *
from celery import app
CELERY_BEAT_SCHEDULE = "django_celery_beat.schedulers.DatabaseScheduler"