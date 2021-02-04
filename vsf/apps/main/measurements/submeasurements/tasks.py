from __future__ import absolute_import, unicode_literals

# Django imports
from django.core.cache import cache

# Third party imports
from celery import shared_task

# Local imports
from .utils         import count_flags_sql, hard_flag
from vsf.utils      import ProcessState, VSFTask
from .FlagsUtils    import *

class SUBMEASUREMENTS_TASKS:
    COUNT_FLAGS = 'count_flags'
    HARD_FLAGS  = 'hard_flags'
    
@shared_task(time_limit=3600, vsf_name=SUBMEASUREMENTS_TASKS.COUNT_FLAGS, base=VSFTask)
def count_flags_submeasurements():
    name = SUBMEASUREMENTS_TASKS.COUNT_FLAGS
    state = cache.get(name)
    result = {'error' : None, 'ran' : False}

    if state == ProcessState.RUNNING or state == ProcessState.STARTING:
        return result

    cache.set(name, ProcessState.RUNNING)
    try: 
        result['result'] = count_flags_sql()
    except Exception as e:
        result['error'] = str(e)

    result['ran'] = True
    return result

@shared_task(time_limit=3600, vsf_name = SUBMEASUREMENTS_TASKS.HARD_FLAGS, base=VSFTask)
def hard_flag_task():
    name = SUBMEASUREMENTS_TASKS.HARD_FLAGS
    state = cache.get(name)
    result = {'error' : None, 'ran' : False}

    if state == ProcessState.RUNNING or state == ProcessState.STARTING:
        return result

    cache.set(name, ProcessState.RUNNING)

    try:
        result['result'] = hard_flag()
    except Exception as e:
        result['error'] = str(e)

    result['ran'] = True
    return result