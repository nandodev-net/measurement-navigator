#Django imports
from datetime import datetime, timedelta
from django.core.cache import cache
from django.http.response import HttpResponseBadRequest
from django.views.generic           import TemplateView
from django.http                    import JsonResponse
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin
# Local imports
from apps.main.measurements.submeasurements.tasks import count_flags_submeasurements
from apps.api.fp_tables_api.tasks import fp_update, measurement_update
from vsf.utils                      import ProcessState
from vsf.celery                     import transient_queue_name, USER_TASK_PRIORITY

class ControlPanel(VSFLoginRequiredMixin, TemplateView):
    """
        This view presents a set of buttons to run control 
        functions over the database, such as request new data from 
        ooni, count flags, reset flags, etc.

        Returned within context:
            - for each process named P, returns:
                + P : dict containing the following filds:
                        name : process name in our backend
                        state : its current state
                    And the possible values of P:
                        + 'update_fastpath'
                        + 'measurement_recovery'
                        + 'count_flags'
                        + 'soft_flags'

            - states : a dict with every possible state string
                        + STARTING = "starting"
                        + RUNNING  = "running" 
                        + IDLE     = "idle"    
                        + FAILING  = "failing" 
                        + FAILED   = "failed"  
            - control_types : dict with every possible control type string:
                        + FASTPATH = 'fastpath' (trigger a fetch for new measurements in ooni)
                        + MEASUREMENT_RECOVERY = 'measurement_recovery' (trigger a fetch for the missing part of incomplete measurements)
                        + COUNT_FLAGS = 'count_flags' (trigger a flag counting process)
                        + UNKNOWN  = 'unknown'
                These are the only valid strings to be send in post request to request an action

            
        Also, you can perform POST requests to this view, these are the expected 
        parameters:
            - control_type: type of control you want to trigger, the same values as passed
                            in the context through 'control_types' variable
            Depending on the control_type value, different values may be required:
            - 'fastpath' : 
                + since : since date in 'YYYY-mm-dd' format
                + until : since date in 'YYYY-mm-dd' format
                + only_fastpath : string | none = if you want the results to come from the fastpath only.
            - 'measurement_recovery' : None, just try to recover every incomplete measurement
        The POST request will return a json data with some results:
                + result : 
                            ok = The request has been succesfully processed and it is on its way
                        |   running = The request has been succesfully processed, but process was already running
    """
    template_name="control_panel/control_panel.html"
    
    class CONTROL_TYPES:
        FASTPATH = 'fastpath'
        MEASUREMENT_RECOVERY = 'measurement_recovery'
        COUNT_FLAGS = 'count_flags'
        UNKNOWN  = 'unknown'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update_fastpath'] = {
                                    'name' : fp_update.vsf_name,
                                    'state': cache.get(fp_update.vsf_name)
                                }
        context['measurement_recovery'] = {
            'name' : measurement_update.vsf_name,
            'state': cache.get(measurement_update.vsf_name)
        }

        context['count_flags'] = {
            'name' : count_flags_submeasurements.vsf_name,
            'state': cache.get(count_flags_submeasurements.vsf_name)
        }

        context['states'] = ProcessState.__dict__
        context['control_types'] = self.CONTROL_TYPES.__dict__
        return context

    def post(self, request, *args, **kwargs):
        """
            Return a result based on the following possible outcomes:
                result :=
                        ok : The process started to run succesfully
                    |   already_running : didn't started the process since it was already running       
        """
        # Define possible responses
        OK = 'ok'
        RUNNING = 'already_running'

        # Map from control panel options to function names
        process_names = {
            self.CONTROL_TYPES.FASTPATH : fp_update.vsf_name, # vsf_name is a custom attribute that every vsf task should fill 
            self.CONTROL_TYPES.MEASUREMENT_RECOVERY : measurement_update.vsf_name,
            self.CONTROL_TYPES.COUNT_FLAGS : count_flags_submeasurements.vsf_name,
        }   

        # Get request data 
        req = request.POST
        control = req.get('control_type')

        # Check the state; if process is not running and not failed, then it is busy right now, 
        # try not to run it
        state = cache.get(process_names.get(control, self.CONTROL_TYPES.UNKNOWN), ProcessState.UNKNOWN)
        if state != ProcessState.IDLE and state != ProcessState.FAILED and state != ProcessState.UNKNOWN:
            return JsonResponse({"result" : RUNNING}) 

        # Perform different actions depending on the control triggered
        # Fastpath update
        if control == ControlPanel.CONTROL_TYPES.FASTPATH:

            # Look since parameter
            since = req.get('since')
            if not since:
                # If since parameters is not provided, take "today at 00:00" as since
                since = datetime.now().strftime('%Y-%m-%d')

            # Look until parameter
            until = req.get('until')
            if not until:
                # if until parameter is not provided, take "today at midnight" as until
                until = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

            # Get 'only_fastpath parameter', we just care if it is none or not
            only_fastpath = req.get('only_fastpath') is not None

            # run task
            fp_update.apply_async(
                                kwargs = {  'until' : until, 
                                            'since' : since, 
                                            'only_fastpath' : only_fastpath
                                        }, 
                                queue=transient_queue_name, 
                                priority=USER_TASK_PRIORITY)
            return JsonResponse ( {"result" : OK} )
        # Measurement recovery
        elif control == ControlPanel.CONTROL_TYPES.MEASUREMENT_RECOVERY:
            # Just run task
            measurement_update.apply_async( queue=transient_queue_name, priority=USER_TASK_PRIORITY)            
            return JsonResponse( {"result" : OK} )
        # Count flags
        elif control == ControlPanel.CONTROL_TYPES.COUNT_FLAGS:
            count_flags_submeasurements.apply_async( queue=transient_queue_name, priority=USER_TASK_PRIORITY )
            return JsonResponse( {"result" : OK} )    

        return JsonResponse( {"result" : OK} )

def get_process_state(request):
    """
        Given a list of process names within a post request, return 
        a dict with each process name related to its state 
        This view will reject non-post requests. Expected arguments:
            + process : [str] = a list of process whose state you want to know, they should match 
                                their corresponding vsf_name attribute
        
        returns:
            + process_stats : {process : status} = a dict that maps from process to their current status.
                Note that "process" is as specified in the request, and "status" could be one of the values
                specified in ProcessState in vsf.utils. If a process is actually unknown by the system, 
                'ProcessStatus.UNKNOWN' will be returned for this process
    """
    if not request.POST:
        return HttpResponseBadRequest()
    
    req = request.POST
    process_list = list(req.getlist('process[]'))
    ans = {}
    for process in process_list:
        ans[process] = cache.get(process, ProcessState.UNKNOWN)
    return JsonResponse({ "process_status" : ans })
    