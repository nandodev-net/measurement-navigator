"""
    This file is required by celery to perform the asynchronous process,
    add them in the schedule below.
"""

from __future__ import absolute_import, unicode_literals

import os

from datetime import datetime, timedelta
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vsf.settings.production')

app = Celery('vsf')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# day variable

now = datetime.now()
yesterday = now - timedelta(days=1)


app.conf.beat_schedule = {
    # fp update to search for new recent measurements in the fast path
    'update-fastpath':{
        'task': 'apps.api.fp_tables_api.tasks.fp_update',
        'schedule':3600,
        'args':(None, None, False)
    },
    # measurement_update to check for complete measurements to download
    'update-measurements':{
        'task':'apps.api.fp_tables_api.tasks.measurement_update',
        'schedule':600,
        'args':()
    },
    # SoftFlagMeasurement updates the possible flags for every sub measurement
    'update-soft-flags':{
        'task':'apps.main.measurements.submeasurements.tasks.SoftFlagMeasurements',
        'schedule':3600,
        'args':()
    },
    # Count Flags submeasurements updates the value of previous_counter field in submeasurements
    # field
    'update-hf-counters':{
        'task':'apps.main.measurements.submeasurements.tasks.count_flags_submeasurements',
        'schedule':3600,
        'args':()
    },
    # Run the hard flag algorithm over all the measurements
    'update-hard-flags':{
        'task':'apps.main.measurements.submeasurements.tasks.count_flags_submeasurements',
        'schedule':3600,
        'args':()
    },
    
}

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
