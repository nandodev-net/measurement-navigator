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
from apps.api.fp_tables_api.tasks   import fp_update
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update_fastpath'] = {
                                    'name' : fp_update.name,
                                    'state': cache.get(fp_update.name)
                                }

        context['states'] = ProcessState.__dict__
        
        return context

    def post(self, request, *args, **kwargs):
        req = request.POST
        since = req.get('since')
        until = req.get('until')
        only_fastpath = req.get('only_fastpath') is not None
        control = req.get('control_type')
        if control == ControlPanel.CONTROL_TYPES.FASTPATH:
            date_format = "%Y-%m-%d"
            since = datetime.strptime(since, date_format)
            until = datetime.strptime(until, date_format)

            return fp_update.delay(since, until)
        return JsonResponse( {"result":"everything ok"} )

    
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
        ans[process] = cache.get(process)
        print(f"{process} : {ans[process]}")
    return JsonResponse({ "process_status" : ans })
    