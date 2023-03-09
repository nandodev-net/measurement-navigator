from __future__ import absolute_import, unicode_literals

# Django imports
from django.core.cache import cache

# Third party imports
from celery import shared_task

# Local imports
from .utils              import count_flags_sql, hard_flag
from vsf.utils           import ProcessState, VSFTask
from .flags_utils         import *
from apps.configs.models import Config
from apps.main.measurements.submeasurements.models import SUBMEASUREMENTS

class SUBMEASUREMENTS_TASKS:
    COUNT_FLAGS = 'count_flags'
    HARD_FLAGS  = 'hard_flags'

# maybe deprecated, merged with hard_flag_task 
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
    """
        Task to perform a hard flag detecting algorithm. 
        First flags should be counted, then the hard flag algorithm itself will run,
        and finally we update every flag end and initial date
    """

    name = SUBMEASUREMENTS_TASKS.HARD_FLAGS
    state = cache.get(name)
    result = {'error' : None, 'ran' : False}

    if state == ProcessState.RUNNING or state == ProcessState.STARTING:
        return result

    cache.set(name, ProcessState.RUNNING)

    # parse config
    config = Config.get()
    if config:
        delta = timedelta(days=config.hardflag_timewindow)  
        openning_treshold = config.hardflag_openning_treshold 
        continue_treshold = config.hardflag_continue_treshold
        interval_size = config.hardflag_interval_size
    else:
        delta = timedelta(days=2)
        openning_treshold = 7
        continue_treshold = 4
        interval_size = 10

    try:
        result['counted'] = count_flags_sql()                                                       # count flags
        result['result']  = hard_flag(delta, openning_treshold, interval_size, continue_treshold)   # Perform a flag detecting algorithm
        update_event_dates()                                                                        # update events 
    except Exception as e:
        result['error'] = str(e)

    result['ran'] = True
    return result

@shared_task(time_limit=3600)
def ping_database():
    """Just a test task to try ping the database looking for the newest 100 measurements
    for each submeasurement. We do this because the web page becomes slow after a few 
    time without any query, so we want to test if doing a few querys once in a while
    keeps the site from slowing down
    """

    for SBMS in SUBMEASUREMENTS:
        SBMS : Type[SubMeasurement] = SBMS
        list(SBMS.objects.all().order_by('time')[:100])
