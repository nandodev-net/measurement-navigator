from __future__ import absolute_import, unicode_literals

# Django imports
from django.core.cache import cache

# Third party imports
from celery import shared_task
from django.views.generic import base

# Local imports
from .utils         import SoftFlag, count_flags_sql, hard_flag
from vsf.utils      import ProcessState, VSFTask
from .FlagsUtils    import *

class SUBMEASUREMENTS_TASKS:
    COUNT_FLAGS = 'count_flags'
    SOFT_FLAGS  = 'soft_flags'
    HARD_FLAGS  = 'hard_flags'

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

@shared_task(time_limit=3600, vsf_name = SUBMEASUREMENTS_TASKS.HARD_FLAGS, base=VSFTask)
def hard_flag_task():
    # Get the data we need, all the submeasurements ordered by input, and by date
    submeasurements = [(HTTP,'http'), (TCP,'tcp'), (DNS, 'dns')]

    # just a shortcut
    start_time = lambda m : m.measurement.raw_measurement.measurement_start_time

    result = {'hard_tagged':[]}
    # For every submeasurement type...
    for (SM, label) in submeasurements:

        meas = SM.objects.raw(
            (   "SELECT " +
                "submeasurements_{label}.id, " +
                "previous_counter, " +
                "rms.measurement_start_time, " +
                "dense_rank() OVER (order by rms.input) as group_id " +

                "FROM " +
                "submeasurements_{label} JOIN measurements_measurement ms ON ms.id = submeasurements_{label}.measurement_id " +
                                        "JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id " +
                                        "JOIN flags_flag f ON f.id = submeasurements_{label}.flag_id " +
                "WHERE " +
                "f.flag<>'ok' " +
                "ORDER BY rms.input, rms.measurement_start_time, previous_counter; "
            ).format(label=label)
        )
        
        groups = Grouper(meas, lambda m: m.group_id)


        for group in groups:
            start_time = time()
            result = select(group)
            elapsed_time = time() - start_time
            print(elapsed_time)
            print(result)
            merge(result)