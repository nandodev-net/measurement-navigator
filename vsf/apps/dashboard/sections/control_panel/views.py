#Django imports
from datetime import datetime
from celery.app import shared_task
from django.core.cache import cache
from django.http.response import HttpResponseBadRequest
from django.views.generic           import TemplateView, View
from django.http                    import JsonResponse
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
# Local imports
from vsf.tasks                      import fp_update
from vsf.utils                      import ProcessState

class ControlPanel(VSFLoginRequiredMixin, TemplateView):
    """
        This view presents a set of buttons to run control 
        functions over the database, such as request new data from 
        ooni, count flags, reset flags, etc.
    """
    template_name="control_panel/control_panel.html"
    
    class CONTROL_TYPES:
        FASTPATH = 'fastpath'
        UNKNOWN  = 'unknown'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update_fastpath'] = {
                                    'name' : fp_update.name,
                                    'state': cache.get(fp_update.name)
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
            self.CONTROL_TYPES.FASTPATH : fp_update.name,
        }

        # Get request data 
        req = request.POST
        control = req.get('control_type')

        # Check the state; if process is not running and not failed, then it is busy right now, 
        # try not to run int
        state = cache.get(process_names.get(control, self.CONTROL_TYPES.UNKNOWN))
        if state != ProcessState.IDLE and state != ProcessState.FAILED:
            return JsonResponse({"result" : RUNNING}) 

        # Perform different actions depending on the control triggered
        if control == ControlPanel.CONTROL_TYPES.FASTPATH:
            since = req.get('since')
            until = req.get('until')
            only_fastpath = req.get('only_fastpath') is not None
            fp_update.apply_async(kwargs = {'until' : until, 'since' : since})
            return JsonResponse ( {"result" : OK} )


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
        print(f"{process} : {ans[process]}")
    return JsonResponse({ "process_status" : ans })
    