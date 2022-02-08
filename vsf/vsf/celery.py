"""
    This file is required by celery to perform the asynchronous process,
    add them in the schedule below.
"""
# Third party imports
from __future__     import absolute_import, unicode_literals
import os
from datetime       import datetime, timedelta
from celery         import Celery
from kombu          import Queue, Exchange

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vsf.settings.production')

app = Celery('vsf')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')


# --------- Create custom queues --------- #
#   Priorities:
USER_TASK_PRIORITY = 6
DEFAULT_PRIORITY   = 5
TASK_MAX_PRIORITY  = 10

#   Transient queue: Used for non-persistent tasks (almost every task)
transient_queue_name    = 'transient'
transient_routing_key   = 'transient'
transient_exchange_name = 'transient'

transient_exchange      = Exchange(transient_exchange_name, delivery_mode=1) # Delivery mode = 1 means non persistent

transient_queue = Queue(    transient_queue_name, 
                            transient_exchange, 
                            routing_key=transient_routing_key, 
                            durable=False,
                            queue_arguments={'x-max-priority': TASK_MAX_PRIORITY}
                        )

#   Transient user queue: Used for non-persistent user-requested tasks, they have higher priority than
#   automated tasks  
user_transient_queue_name    = 'user_transient'
user_transient_routing_key   = 'user_transient'

user_transient_queue = Queue(   user_transient_queue_name,
                                transient_exchange,
                                routing_key=user_transient_routing_key,
                                durable=False,
                                queue_arguments={'x-max-priority': TASK_MAX_PRIORITY}
                            )

#   Default queue: Celery queue
celery_queue_name  = 'celery' # default one
celery_routing_key = 'celery'

celery_queue = Queue(
                        celery_queue_name, 
                        routing_key=celery_routing_key,
                    )

#   Register queues
app.conf.task_queues = (transient_queue, user_transient_queue, celery_queue)



# --------- Celery Beat config: Set up periodic tasks --------- #
app.conf.beat_schedule = {
    # fp update to search for new recent measurements in the fast path
    'update-fastpath':{
        'task': 'apps.api.fp_tables_api.tasks.fp_update',
        'schedule':3600,
        'args':(None, None, False),
        'options' : {'queue' : transient_queue_name}
    },
    # measurement_update to check for complete measurements to download
    'update-measurements':{
        'task':'apps.api.fp_tables_api.tasks.measurement_update',
        'schedule':3600,
        'args':(),
        'options' : {'queue' : transient_queue_name}
    },
    'update-hard-flags':{
        'task':'apps.main.measurements.submeasurements.tasks.hard_flag_task',
        'schedule':7200,
        'args':(),
        'options' : {'queue' : user_transient_queue_name}
    },
    'update-case-dates':{
        'task':'apps.main.cases.tasks.update_case_dates',
        'schedule':3600,
        'args' : (),
        'options' : {'queue' : transient_queue_name}
    }
}


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

