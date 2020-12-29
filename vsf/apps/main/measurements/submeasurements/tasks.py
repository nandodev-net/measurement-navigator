from __future__ import absolute_import, unicode_literals
from celery import shared_task

from .utils import SoftFlag, count_flags_sql, hard_flag


@shared_task(time_limit=3600)
def SoftFlagMeasurements():
    return SoftFlag(limit=5000)
    

@shared_task(time_limit=3600)
def count_flags_submeasurements():
    return count_flags_sql()

@shared_task(time_limit=1800)
def hard_flag_task():
    return hard_flag()