"""
    Utility functions to use throughout the project.
"""
# Django imports
from django.db.models       import OuterRef, Subquery
from django.db.models.query import QuerySet
from django.core.cache      import cache

# Third party imports
from celery.worker.request  import Request
from celery.app.task        import Task

# Local imports
from apps.main.measurements.models  import Measurement, RawMeasurement
from apps.main.sites.models         import Site, URL

def MeasurementXRawMeasurementXSite() -> QuerySet:
    """
        Join measurement with raw measurement and its corresponding site.
        The site member it's available with the 'site' name.

        example:
        qs = MeasurementXRawMeasurementXSite()
        qs[0].site == foreign key to a site if it exist, None otherwise
    """

    urls = URL.objects.all().select_related('site').filter(url=OuterRef('raw_measurement__input'))
    qs   = Measurement.objects.all()\
                .select_related('raw_measurement')\
                .annotate(
                        site=Subquery(urls.values('site')),
                        site_name=Subquery(urls.values('site__name'))
                    )

    return qs


# --- Process management --- # 

class ProcessState:
    """
        Enum defining every possible state for a process
    """
    STARTING= "starting"# process accepted and about to start
    RUNNING = "running" # process started
    IDLE    = "idle"    # process not running
    FAILING = "failing" # process shows some problems
    FAILED  = "failed"  # last time the process ran, it failed

class VSFRequest(Request):
    """
        This kind of request allows us to customize the process behavior. 
        We use this so we can perform custom actions when a process starts running,
        crashes, gets tle etc.

        For now, the custom behavior is to setup a cached variable defining the process state,
        defined by the ProcessState enum
    """
    def on_timeout(self, soft, timeout):
        name = self.task_name 

        # If for some reason this task's name is not registered, register it
        if cache.get(name) is None:
            cache.set(name, ProcessState.RUNNING)
        
        # If process is not going to end, register a possibly-failure state
        if soft:
            cache.set(name, ProcessState.FAILING)
        # otherwise, the process is going to end so set it to idle
        else:
            cache.set(name, ProcessState.FAILED)

        return super().on_timeout(soft, timeout)

    def on_failure(self, exc_info, send_failed_event, return_ok):
        name = self.task_name 

        # If for some reason this task's name is not registered, register it
        if cache.get(name) is None:
            cache.set(name, ProcessState.RUNNING)
        
        
        cache.set(name, ProcessState.FAILED)

        return super().on_failure(exc_info, send_failed_event=send_failed_event, return_ok=return_ok)

    def on_accepted(self, pid, time_accepted):
        cache.set(self.task_name, ProcessState.STARTING)
        return super().on_accepted(pid, time_accepted)

    def on_success(self, failed__retval__runtime, **kwargs):
        cache.set(self.task_name, ProcessState.IDLE)
        return super().on_success(failed__retval__runtime, **kwargs)

class VSFTask(Task):
    """
        Every task inheriting this class will report itself to 
        cache so we can query if it is running at any time
    """
    Request = VSFRequest

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        cache.set(self.task_name, ProcessState.IDLE)
        return super().after_return(status, retval, task_id, args, kwargs, einfo)