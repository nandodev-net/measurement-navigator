from __future__ import absolute_import, unicode_literals

# Django imports
from django.core.cache import cache

# Third party imports
from celery import shared_task

# Local imports
from vsf.utils           import ProcessState, VSFTask
from apps.configs.models import Config
from .models             import Case
from datetime            import datetime, timedelta


class CASES_TASKS:
    UPDATE_DATES = 'update_dates'


@shared_task(time_limit=86400, vsf_name = CASES_TASKS.UPDATE_DATES, base=VSFTask)
def update_case_dates():
    """
        Task that runs for all over the cases and detect if 
        there was a change in their associated events dates, in
        order to update them.
    """

    name = CASES_TASKS.UPDATE_DATES
    #state = cache.get(name)
    result = {'error' : None, 'ran' : False}

    # if state == ProcessState.RUNNING or state == ProcessState.STARTING:
    #     return result

    #cache.set(name, ProcessState.RUNNING)

    try:
        for case in Case.objects.all():
            if case.start_date_automatic or case.end_date_automatic:

                ordered_by_start_date = case.events.order_by('start_date')
                ordered_by_end_date = case.events.order_by('end_date')
                start_date_automatic = ordered_by_start_date.first().start_date.replace(tzinfo=None) or None
                end_date_automatic = ordered_by_end_date.last().end_date.replace(tzinfo=None) or None

                is_active = case.is_active
                if end_date_automatic > datetime.now(): is_active = True
                else: is_active = False

                if case.start_date_manual and case.end_date_manual:
                    case.update(
                        start_date_automatic = start_date_automatic,
                        end_date_automatic = end_date_automatic
                    )
                elif not (case.start_date_manual and case.end_date_manual):
                    case.update(
                        start_date_automatic = start_date_automatic,
                        end_date_automatic = end_date_automatic,
                        start_date = start_date_automatic,
                        end_date = end_date_automatic,
                        active = is_active,
                    )

    except Exception as e:
        result['error'] = str(e)

    result['ran'] = True
    return result