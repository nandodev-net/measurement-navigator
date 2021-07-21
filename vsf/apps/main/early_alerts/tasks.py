from __future__ import absolute_import, unicode_literals

# Django imports
from django.core.cache import cache

# Third party imports
from celery import shared_task

# Local imports
from vsf.utils      import ProcessState, VSFTask
from .utils         import update_last_anomaly_rate_on_config

class EARLY_ALERTS_TASKS:
    CHECK_ANOMALY_RATE = "anomaly_rate"
    
@shared_task(time_limit=3600, vsf_name=EARLY_ALERTS_TASKS.CHECK_ANOMALY_RATE, base=VSFTask)
def check_anomaly_rate():
    name = EARLY_ALERTS_TASKS.CHECK_ANOMALY_RATE    
    state = cache.get(name)
    result = {'error' : None, 'ran' : False}

    if state == ProcessState.RUNNING or state == ProcessState.STARTING:
        return result

    cache.set(name, ProcessState.RUNNING)
    try: 
        result['result'] = update_last_anomaly_rate_on_config()
    except Exception as e:
        result['error'] = str(e)

    result['ran'] = True
    return result