"""
    This file contains every task definition
"""
# Django imports
from django.core.cache  import cache

# Third party imports 
from __future__         import absolute_import, unicode_literals
from datetime           import datetime, timedelta
from celery             import shared_task

# Local imports
from apps.api.fp_tables_api.utils                   import request_fp_data, update_measurement_table
from vsf.utils                                      import VSFTask, ProcessState
from apps.main.measurements.submeasurements.utils   import SoftFlag, hard_flag, count_flags_sql

class VSF_TASK:
    FP_UPDATE           = "update-fastpath"
    MEASUREMENT_UPDATE  = "measurement-update"
    SOFT_FLAG           = "soft-flag-measurement"
    COUNT_FLAGS         = "count-flags"
    HARD_FLAG           = "hard-flag"     

@shared_task(time_limit=3600, name=VSF_TASK.FP_UPDATE, base=VSFTask)
def fp_update(since : str = None, until : str = None, only_fastpath : bool = False):
    """
        Update the fast path table;
        This function will request fast path table to the ooni api
        from  yesterday until the currently running day.
    """
    
    # Idempotency
    state = cache.get("update-fastpath")
    if state == ProcessState.RUNNING:
        return
    date_format = "%Y-%m-%d"
    # note that we use "now" as tomorrow, because the request truncates 
    # the "time" part of the datetime, so the ooni query will search
    # until the next day at the 00:00:00 hour, including 'today' in the query,
    # but excluding "tomorrow".
    # [     interval      ]
    # | yesterday | today | tomorrow 
    cache.set("update-fastpath", ProcessState.RUNNING)
    if until is None:
        until = datetime.now() + timedelta(days=1)
        until = datetime.strftime(until, date_format)

    if since is None:
        until_datetime = datetime.strptime(until, date_format)
        since = until_datetime - timedelta(days=1)
        since = datetime.strftime(since, date_format)
    
    try: 
        request_fp_data(since, until, only_fastpath)
        cache.set("update-fastpath", ProcessState.IDLE)
    except Exception as e:
        cache.set("update-fastpath", ProcessState.FAILED + " : " + str(e) + f". Args: {since}, {until}")
    
    
@shared_task(time_limit=2000, name="recover-measurements")
def measurement_update():
    """
        Update Measurement table by requesting for new measurements availables
        in the fast path. If there's too many measurements, it's recommended to 
        request a small ammount of them periodically rather than requesting them 
        all at the same time
    """
    #note that there's currently infinite retrys, since we have a problem retrieving data from ooni
    return update_measurement_table(200) 

@shared_task(time_limit=3600)
def SoftFlagMeasurements():
    return SoftFlag(limit=5000)
    

@shared_task(time_limit=600)
def count_flags_submeasurements():
    return count_flags_sql()

@shared_task(time_limit=1800)
def hard_flag_task():
    return hard_flag()
