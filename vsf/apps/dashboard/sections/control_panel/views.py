#Django imports
from django.views.generic           import TemplateView, View
from django.http                    import JsonResponse
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
# Local imports
from apps.api.fp_tables_api.utils   import request_fp_data

class ControlPanel(VSFLoginRequiredMixin, TemplateView):
    """
        This view presents a set of buttons to run control 
        functions over the database, such as request new data from 
        ooni, count flags, reset flags, etc.
    """
    template_name="control_panel/control_panel.html"
    
    class CONTROL_TYPES:
        FASTPATH = 'fastpath'

    def post(self, request, *args, **kwargs):
        req = request.POST
        since = req.get('since')
        until = req.get('until')
        only_fastpath = req.get('only_fastpath') is not None
        control = req.get('control_type')
        if control == ControlPanel.CONTROL_TYPES.FASTPATH:
            return self.update_fastpath(since, until, only_fastpath)

        return JsonResponse({"result":"everything ok"})
    
    def update_fastpath(self, since, until, only_fastpath):
        (status, returned) = request_fp_data(since, until, only_fastpath)
        if status != 200:
            return JsonResponse({"error" : "No se pudo contactar con ooni", "results" : None})

        return JsonResponse({"error" : None, "results" : returned})