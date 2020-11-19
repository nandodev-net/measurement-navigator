from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time
from datetime import datetime, timedelta

from .utils import request_fp_data, update_measurement_table

# @TODO Delete later, we use this to check whether the process are running
@shared_task
def sum (a,b):
    time.sleep(2)
    return a+b
    
@shared_task(time_limit=750)
def fp_update():
    """
        Update the fast path table;
        This function will request fast path table to the ooni api
        from  yesterday until the currently running day.
    """
    
    # note that we use "now" as tomorrow, because the request truncates 
    # the "time" part of the datetime, so the ooni query will search
    # until the next day at the 00:00:00 hour, including 'today' in the query,
    # but excluding "tomorrow".
    # [     interval      ]
    # | yesterday | today | tomorrow 
    now = datetime.now() + timedelta(days=1)
    yesterday = now - timedelta(days=1)
    return request_fp_data(yesterday.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"), False)
    
@shared_task(time_limit=750)
def measurement_update():
    """
        Update Measurement table by requesting for new measurements availables
        in the fast path. If there's too many measurements, it's recommended to 
        request a small ammount of them periodically rather than requesting them 
        all at the same time
    """
    #note that there's currently infinite retrys, since we have a problem retrieving data from ooni
    return update_measurement_table(200) 

