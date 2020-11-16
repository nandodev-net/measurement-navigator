from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time
from datetime import datetime, timedelta

from .utils import SoftFlag


@shared_task
def SoftFlagMeasurements():
    return SoftFlag()
    