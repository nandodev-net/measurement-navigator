#Django imports
from datetime import datetime, timedelta
from celery.app import shared_task
from django.core.cache import cache
from django.http.response import HttpResponseBadRequest
from django.views.generic           import TemplateView, View
from django.http                    import JsonResponse
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
# Local imports
from vsf.vsf_tasks                  import fp_update, measurement_update
from vsf.utils                      import ProcessState

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

            - states : a dict with every possible state string
                        + STARTING = "starting"
                        + RUNNING  = "running" 
                        + IDLE     = "idle"    
                        + FAILING  = "failing" 
                        + FAILED   = "failed"  
            - control_types : dict with every possible control type string:
                        + FASTPATH = 'fastpath' (trigger a fetch for new measurements in ooni)
                        + MEASUREMENT_RECOVERY = 'measurement_recovery' (trigger a fetch for the missing part of incomplete measurements)
                        + UNKNOWN  = 'unknown'

            
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
        }   

        # Get request data 
        req = request.POST
        control = req.get('control_type')

        # Check the state; if process is not running and not failed, then it is busy right now, 
        # try not to run int
        state = cache.get(process_names.get(control, self.CONTROL_TYPES.UNKNOWN), ProcessState.UNKNOWN)
        if state != ProcessState.IDLE and state != ProcessState.FAILED and state != ProcessState.UNKNOWN:
            return JsonResponse({"result" : RUNNING}) 

        # Perform different actions depending on the control triggered
        if control == ControlPanel.CONTROL_TYPES.FASTPATH:

            # Look since parameter
            since = req.get('since')
            if not since:
                # If since parameters is not provided, take "today at 00:00" as since
                since = datetime.now().strftime('%Y-%m-%d')

            #look until parameter
            until = req.get('until')
            if not until:
                # if until parameter is not provided, take "today at midnight" as until
                until = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

            only_fastpath = req.get('only_fastpath') is not None
            print(f"Updating fastpath with since = {since}, until = {until}, only_fastpath = {only_fastpath}")
            fp_update.apply_async(kwargs = {'until' : until, 'since' : since, 'only_fastpath' : only_fastpath})
            return JsonResponse ( {"result" : OK} )
        elif control == ControlPanel.CONTROL_TYPES.MEASUREMENT_RECOVERY:
            measurement_update.apply_async()
            
            print("\u001b[31mRecovering missing measurements\u001b[0m")
            return JsonResponse( {"result" : OK} )

        return JsonResponse( {"result" : OK} )

    
    #def update_fastpath(self, since, until, only_fastpath):
    #    (status, returned) = request_fp_data(since, until, only_fastpath)
    #    if status != 200:
    #        return JsonResponse({"error" : "No se pudo contactar con ooni", "results" : None})
#
    #    return JsonResponse({"error" : None, "results" : returned})

def get_process_state(request):
    """
        Given a list of process names within a post request, return 
        a dict with each process name related to its state 
    """
    if not request.POST:
        return HttpResponseBadRequest()
    
    req = request.POST
    process_list = list(req.getlist('process[]'))
    ans = {}
    for process in process_list:
        ans[process] = cache.get(process) or "unknown state"
    return JsonResponse({ "process_status" : ans })
    