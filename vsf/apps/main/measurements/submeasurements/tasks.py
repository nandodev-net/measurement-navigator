from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time
from datetime import datetime, timedelta

from .utils import SoftFlag, count_flags


@shared_task
def SoftFlagMeasurements():
    return SoftFlag(limit=1000)
    

@shared_task
def count_flags_submeasurements():
    return count_flags()