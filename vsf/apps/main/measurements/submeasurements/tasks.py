from __future__ import absolute_import, unicode_literals

# Django imports
from django.core.cache import cache

# Third party imports
from celery import shared_task
from django.views.generic import base

# Local imports
from .utils         import SoftFlag, count_flags_sql, hard_flag
from vsf.utils      import ProcessState, VSFTask

class SUBMEASUREMENTS_TASKS:
    COUNT_FLAGS = 'count_flags'
    SOFT_FLAGS  = 'soft_flags'

@shared_task(time_limit=3600, vsf_name = SUBMEASUREMENTS_TASKS.SOFT_FLAGS, base=VSFTask)
def SoftFlagMeasurements(since : str = None, until : str = None, limit : int = 5000, page_size : int = 1000, absolute : bool = False ):

    name = SUBMEASUREMENTS_TASKS.SOFT_FLAGS
    state = cache.get(name)
    result = {'error' : None, 'ran' : False}
    
    if state == ProcessState.RUNNING or state == ProcessState.STARTING:
        return result

    cache.set(name, ProcessState.RUNNING)

    try:
        result['result'] = SoftFlag(since, until, limit, page_size, absolute)
    except Exception as e:
        result['error'] = str(e)

    result['ran'] = True
    return result 
    
@shared_task(time_limit=3600, vsf_name=SUBMEASUREMENTS_TASKS.COUNT_FLAGS, base=VSFTask)
def count_flags_submeasurements():
    state = cache.get(SUBMEASUREMENTS_TASKS.COUNT_FLAGS)
    result = {'error' : None, 'ran' : False}

    if state == ProcessState.RUNNING or state == ProcessState.STARTING:
        return result

    cache.set(SUBMEASUREMENTS_TASKS.COUNT_FLAGS, ProcessState.RUNNING)
    try: 
        result['result'] = count_flags_sql()
    except Exception as e:
        result['error'] = str(e)

    result['ran'] = True
    return result

@shared_task(time_limit=1800)
def hard_flag_task():
    return hard_flag()