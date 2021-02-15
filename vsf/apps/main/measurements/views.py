# Django imports
from django.shortcuts       import render
from django.http            import JsonResponse, Http404, HttpResponseBadRequest
from django.views.generic   import View

# Local imports
from .models                import Measurement
from vsf.views              import VSFLoginRequiredMixin 
from apps.main.measurements.submeasurements     import models as SubMModels

# Create your views here.
class GetMeasurement(VSFLoginRequiredMixin, View):
    """
        This view retrieves a measurement in json data format
        Expected GET arguments:
            id = measurement id whose details are to be retireved
    """
    def get(self, request, **kwargs):
        id = request.GET.get('id')
        if id == None:
            return HttpResponseBadRequest("Missing 'id' argument")

        try:
            m = Measurement.objects.get(id=id)
        except Measurement.DoesNotExist:
            return Http404()

        # Delete this useless member variable
        d = m.raw_measurement.__dict__
        ok_flag = SubMModels.SubMeasurement.FlagType.OK
        flagsDNS  = any(subm.flag_type != ok_flag for subm in m.dns_set.all())
        flagsHTTP = any(subm.flag_type != ok_flag for subm in m.http_set.all())
        flagsTCP  = any(subm.flag_type != ok_flag for subm in m.tcp_set.all())
        d['flags'] = {'dns': flagsDNS, 'http': flagsHTTP, 'tcp': flagsTCP}
        del d['_state']
        return JsonResponse(d)