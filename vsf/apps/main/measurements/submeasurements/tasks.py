from __future__ import absolute_import, unicode_literals

# Django imports
from django.core.cache import cache

# Third party imports
from celery import shared_task

# Local imports
from .utils         import SoftFlag, count_flags_sql, hard_flag
from vsf.utils      import ProcessState

class SUBMEASUREMENTS_TASKS:
    COUNT_FLAGS = 'count_flags'

@shared_task(time_limit=3600)
def SoftFlagMeasurements():
    return SoftFlag(limit=5000)
    
@shared_task(time_limit=3600, vsf_name=SUBMEASUREMENTS_TASKS.COUNT_FLAGS)
def count_flags_submeasurements():
    state = cache.get(SUBMEASUREMENTS_TASKS.COUNT_FLAGS)
    if state == ProcessState.RUNNING:
        return
    result = {'error' : None}
    try: 
        result['output']=cache.set(SUBMEASUREMENTS_TASKS.COUNT_FLAGS, ProcessState.RUNNING)     
    except Exception as e:
        result['error'] = e

    return result

@shared_task(time_limit=1800)
def hard_flag_task():
    return hard_flag()