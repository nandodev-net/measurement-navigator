# Django imports
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.views.generic import View

from vsf.views import VSFLoginRequiredMixin

# Local imports
from .models import Measurement


# Create your views here.
class GetMeasurement(VSFLoginRequiredMixin, View):
    """
    This view retrieves a measurement in json data format
    Expected GET arguments:
        id = measurement id whose details are to be retireved
    """

    def get(self, request, **kwargs):
        id = request.GET.get("id")
        if id == None:
            return HttpResponseBadRequest("Missing 'id' argument")

        try:
            m = Measurement.objects.get(id=id)
        except Measurement.DoesNotExist:
            return Http404()

        # Delete this useless member variable
        d = m.raw_measurement.__dict__
        flagsDNS = [subm.flag_type for subm in m.dns_list.all()]
        flagsHTTP = [subm.flag_type for subm in m.http_list.all()]
        flagsTCP = [subm.flag_type for subm in m.tcp_list.all()]
        d["flags"] = {"dns": flagsDNS, "http": flagsHTTP, "tcp": flagsTCP}
        del d["_state"]
        return JsonResponse(d)
