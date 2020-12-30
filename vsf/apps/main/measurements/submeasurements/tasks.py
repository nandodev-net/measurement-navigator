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
    SOFT_FLAGS  = 'soft_flags'

@shared_task(time_limit=3600, vsf_name = SUBMEASUREMENTS_TASKS.SOFT_FLAGS)
def SoftFlagMeasurements(since : str = None, until : str = None, limit : int = 5000, page_size : int = 1000, absolute : bool = False ):

    name = SUBMEASUREMENTS_TASKS.SOFT_FLAGS
    state = cache.get(name)
    if state == ProcessState.RUNNING:
        return

    cache.set(name, ProcessState.RUNNING)

    result = {'error' : None}
    try:
        result['output'] = SoftFlag(since, until, limit, page_size, absolute)
    except Exception as e:
        result['error'] = e

    return result 
    
@shared_task(time_limit=3600, vsf_name=SUBMEASUREMENTS_TASKS.COUNT_FLAGS)
def count_flags_submeasurements():
    state = cache.get(SUBMEASUREMENTS_TASKS.COUNT_FLAGS)
    if state == ProcessState.RUNNING:
        return

    cache.set(SUBMEASUREMENTS_TASKS.COUNT_FLAGS, ProcessState.RUNNING)
    result = {'error' : None}
    try: 
        result['output'] = count_flags_sql()
    except Exception as e:
        result['error'] = e

    return result

@shared_task(time_limit=1800)
def hard_flag_task():
    return hard_flag()