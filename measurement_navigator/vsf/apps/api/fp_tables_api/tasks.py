from __future__         import absolute_import, unicode_literals

# Django imports
from django.core.cache  import cache

# Third party imports 
from celery             import shared_task

# Python imports
from datetime           import date, timedelta, datetime
from typing import Optional


# Local imports
from .utils             import request_fp_data, update_measurement_table
from vsf.utils          import VSFTask, ProcessState
from apps.api.fp_tables_api.s3_ingest import S3IngestManager

class API_TASKS:
    UPDATE_FASTPATH = "update-fastpath"
    RECOVER_MEASUREMENTS = "recover-measurements"
    S3_INGEST = "s3-ingest"

@shared_task(time_limit=7200, base=VSFTask, vsf_name = API_TASKS.UPDATE_FASTPATH)
def fp_update(since :  Optional[str] = None, until : Optional[str] = None, only_fastpath : bool = False):
    """
        Update the fast path table;
        This function will request fast path table to the ooni api
        from  yesterday until the currently running day.
    """

    ret = { 'ran' : False } # Required by VSFTask base task class
    name = API_TASKS.UPDATE_FASTPATH
    # Idempotency
    state = cache.get(name)
    if state == ProcessState.RUNNING or state == ProcessState.STARTING:
        return ret

    # This task actually ran 

    date_format = "%Y-%m-%d"
    # note that we use "now" as tomorrow, because the request truncates 
    # the "time" part of the datetime, so the ooni query will search
    # until the next day at the 00:00:00 hour, including 'today' in the query,
    # but excluding "tomorrow".
    # [     interval      ]
    # | yesterday | today | tomorrow 
    cache.set(name, ProcessState.RUNNING)
    if until is None:
        until = datetime.now() + timedelta(days=1)
        until = datetime.strftime(until, date_format)

    if since is None:
        until_datetime = datetime.strptime(until, date_format)
        since = until_datetime - timedelta(days=1)
        since = datetime.strftime(since, date_format)
    
    try: 
        ret['output'] = request_fp_data(since, until, from_fastpath = only_fastpath)
        cache.set(name, ProcessState.IDLE)
    except Exception as e:
        cache.set(name, ProcessState.FAILED)
        ret['error'] = str(e)

    ret['ran'] = True
    return ret
    
    
    
@shared_task(time_limit=2000, vsf_name=API_TASKS.RECOVER_MEASUREMENTS, base=VSFTask)
def measurement_update():
    """
        Update Measurement table by requesting for new measurements availables
        in the fast path. If there's too many measurements, it's recommended to 
        request a small ammount of them periodically rather than requesting them 
        all at the same time
    """
    name = API_TASKS.RECOVER_MEASUREMENTS
    status = cache.get(name)
    result = {'error' : None, 'ran' : False}

    # Check if should run
    if status == ProcessState.RUNNING or status == ProcessState.STARTING:
        return result

    # Set running state properly
    cache.set(name, ProcessState.RUNNING)

    try:
        result['output'] = update_measurement_table(200)
        cache.set(name, ProcessState.IDLE)

    except Exception as e:
        cache.set(name, ProcessState.FAILED)
        result['error'] = str(e)

    # This task actually ran    
    result['ran'] = True

    return  result 

@shared_task(time_limit = 3600 * 24, vsf_name=API_TASKS.S3_INGEST, base=VSFTask)
def s3_ingest_task():
    """
        Download all measurements available from the last 24 hours to now.
    """

    name = API_TASKS.S3_INGEST
    status = cache.get(name)
    result = {'error' : None, "ran" : False}

    # Check if should run 
    if status == ProcessState.RUNNING or status == ProcessState.STARTING:
        return result
    
    # Set running state to running

    cache.set(name, ProcessState.RUNNING)

    # Set up date
    until = date.today() + timedelta(days=1)
    since = until - timedelta(days=1)

    # Try to ingest 
    try:
        s3_ingestor = S3IngestManager()
        s3_ingestor.ingest(first_date=since, last_date=until)
        result['output'] = None
        cache.set(name, ProcessState.IDLE)
    except Exception as e:
        cache.set(name, ProcessState.FAILED)
        result['error'] = str(e)

    result['ran'] = True

    return result
        