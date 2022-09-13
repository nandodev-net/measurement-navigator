"""
    Utility functions to use throughout the project.
"""
# Django imports
from django.db.models       import OuterRef, Subquery
from django.db.models.query import QuerySet
from django.core.cache      import cache
from django.db.models       import Model

# Third party imports
from celery.worker.request  import Request
from celery.app.task        import Task
from urllib.parse           import urlparse

# python imports
from typing                 import List, Type

# Local imports
from apps.main.measurements.models  import Measurement, RawMeasurement
from apps.main.sites.models         import Site, URL

# --- URL helpers --- #

def get_domain(url : str) -> str:
    """
    Summary: Get the domain dame from an URL. For example:
        >>> get_domain("https://www.google.com/some_search")
        'www.google.com'

    params:
        url : str = URL whose domain we want
    return:
        str = Domain corresponding to provided url
    """
    return urlparse(url).netloc

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
    UNKNOWN = "unknown"

class VSFRequest(Request):
    """
        This kind of request allows us to customize the process behavior. 
        We use this so we can perform custom actions when a process starts running,
        crashes, gets tle etc.

        For now, the custom behavior is to setup a cached variable defining the process state,
        defined by the ProcessState enum.

        Note that this class is coupled with VSFTask Class, they should be used together.
    """
    def on_timeout(self, soft, timeout):
        name = self.task.vsf_name

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

    def on_failure(self, exc_info, send_failed_event=True, return_ok=False):
        name = self.task.vsf_name
        # If for some reason this task's name is not registered, register it
        if cache.get(name) is None:
            cache.set(name, ProcessState.RUNNING)
        
        cache.set(name, ProcessState.FAILED)

        return super().on_failure(exc_info, send_failed_event, return_ok)


class VSFTask(Task):
    """
        Every task inheriting this class will report itself to 
        cache so we can query if it is running at any time.
        Note that every VSFTask should return a dict object, 
        and the only mandatory field is "ran", a boolean field
        telling if the function actually ran or just closed on received.
        If not provided or return is not a dict, ran = False will be assumed.
        An 'error' field is also required to check execution correctness. 
        A value of error = None is assumed as correct execution, otherwise 
        is a failed execution
    """
    Request = VSFRequest
    # Id for us to do status checking
    vsf_name = ""

    def on_success(self, retval, task_id, args, kwargs):
        # Set this process as idle
        try:
            ran = retval.get("ran")
            assert ran != None
        except:
            ran = False

        try:
            execution_ok = retval.get("error") is None
        except:
            execution_ok = True

        name = self.vsf_name

        if ran:
            state = ProcessState.IDLE if execution_ok else ProcessState.FAILED
            cache.set(name, state)
            
        return super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Set this process as a failure
        cache.set(self.vsf_name, ProcessState.FAILED)
        return super().on_failure(exc, task_id, args, kwargs, einfo)

# --- Processing models --- # 

class BulkUpdater:
    """Use this class to schedule bulk updates for models
    """

    def __init__(self, model_class : Type[Model], fields_to_update : List[str], bulk_size : int = 1000) -> None:
        assert bulk_size > 0
        assert len(fields_to_update) > 0

        self._bulk_size = bulk_size
        self._model_class = model_class
        self._queued_instances = []
        self._fields_to_update = fields_to_update
    
    def add(self, instance : Model):
        """Add a new instance to the queue to be processed

        Args:
            instance (Model): instance to queue for update
        """
        self._queued_instances.append(instance)
        if len(self._queued_instances) >= self._bulk_size:
            self.save()

    def save(self):
        """Perform a bulk update operation, flushing the queue of instances to update
        """
        if self._queued_instances == []:
            return # return if nothing to do
        
        self._model_class.objects.bulk_update(self._queued_instances, self._fields_to_update)
        self._queued_instances = []

    def __del__(self):
        self.save()


# --- MISC --- #
class Colors:
    """
        This is a class for printing colored strings,
        very useful for printing messages into the terminal
    """
    RESET   = '\u001b[0m'
    RED     = '\u001b[31m'
    GREEN   = '\u001b[32m'
    YELLOW  = '\u001b[33m' 
    BLUE    = '\u001b[34m'
    MAGENTA = '\u001b[35m'
    CYAN    = '\u001b[36m'
    WHITE   = '\u001b[37m'

    @staticmethod
    def color(string : str, color : str) -> str:
        """
            Summary:
                Color the string 'string' with color 'color' (which is defined in this class)
            Params:
                string : str = string to return colored
                color  : str = Color of the output string, defined by one of the color fields of Colors class
            Return:
                A colored string
        """
        return f"{color}{string}{Colors.RESET}"
    
    @staticmethod
    def red(string : str) -> str:
        """
            Summary:
                Return a red-colored version of string 'string'
            Params:
                string : str = string to color
            Return:
                str = colored string
        """
        return Colors.color(string, Colors.RED)
    
    @staticmethod
    def green(string : str) -> str:
        """
            Summary:
                Return a green-colored version of string 'string'
            Params:
                string : str = string to color
            Return:
                str = colored string
        """
        return Colors.color(string, Colors.GREEN)

    @staticmethod
    def yellow(string : str) -> str:
        """
            Summary:
                Return a yellow-colored version of string 'string'
            Params:
                string : str = string to color
            Return:
                str = colored string
        """
        return Colors.color(string, Colors.YELLOW)

    @staticmethod
    def blue(string : str) -> str:
        """
            Summary:
                Return a blue-colored version of string 'string'
            Params:
                string : str = string to color
            Return:
                str = colored string
        """
        return Colors.color(string, Colors.BLUE)

    @staticmethod
    def magenta(string : str) -> str:
        """
            Summary:
                Return a magenta-colored version of string 'string'
            Params:
                string : str = string to color
            Return:
                str = colored string
        """
        return Colors.color(string, Colors.MAGENTA)

    @staticmethod
    def cyan(string : str) -> str:
        """
            Summary:
                Return a cyan-colored version of string 'string'
            Params:
                string : str = string to color
            Return:
                str = colored string
        """
        return Colors.color(string, Colors.CYAN)

    @staticmethod
    def white(string : str) -> str:
        """
            Summary:
                Return a white-colored version of string 'string'
            Params:
                string : str = string to color
            Return:
                str = colored string
        """
        return Colors.color(string, Colors.WHITE)
    
    
    
    
    
    