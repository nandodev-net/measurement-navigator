# Django imports
import datetime
import pytz
from django.shortcuts               import redirect, HttpResponseRedirect
from django.db.models.query         import QuerySet
from django.core.paginator          import Paginator, Page
from django.views.generic           import TemplateView, ListView, View, CreateView
from django.http                    import HttpResponse, JsonResponse

# third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView

# Local imports
from apps.main.asns                             import models as AsnModels
from apps.main.ooni_fp.fp_tables                import models as fp_models
from vsf.views                                  import VSFLoginRequiredMixin, VSFLogin, TZoneSelectorView
import json
from .utils import *

# Aux views
class VSFListPaginate(TemplateView):
    """
        This class is just a TemplateView that provides
        a function to perform pagination easier. It may
        raise an exception if the request arguments are not consistent

        Expected GET Arguments:
            + page = page index to retrieve
            + page_size = number of items per page
    """
    def _paginate(self, query_set : QuerySet ) -> Page:
        get = self.request.GET or {}

        page = get.get('page')
        page_size = get.get('page_size')

        try:
            page = int(page) if page != None and page != "" else 1
        except:
            raise AttributeError('"page" GET request argument is not a valid number. Given: ', page)

        try:
            page_size = int(page_size) if page_size != None and page_size != "" else 10
        except:
            raise AttributeError('"page_size" GET request argument is not a valid number. Given: ', page_size)


        return Paginator(query_set, page_size).get_page(page)



# Dashboard management views
# --- DASHBOARD VIEW --- #
class Dashboard(VSFLoginRequiredMixin, VSFListPaginate):
    """
        Main home view. It shows the recent data collected by the fast path.
        Expected GET arguments:
            since: minimum time for the measurements
            until: maximum time for the measurements
            asn:   asn that the measurement must have
            testName: value for the test_name field in the measurement
            input: substring that the measurement input should contain
            anomaly: boolean indicating if the measurement presents anomalies or not
            page: number of the page to be showed
            page_size: number of items per page
    """
    template_name = "index.html"

    def dispatch(self, request, *args, **kwargs):
        
        if request.user.is_authenticated and request.user.raw_pss:
            return HttpResponseRedirect("/dashboard/users/createpass/"+str(request.user.id))
        else:
            return super(Dashboard, self).dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):

        try:
            self.request.session['system_tz'] = self.request.session['system_tz'] 
        except:
            self.request.session['system_tz'] = "2"

        # Get parent context:
        context = super().get_context_data(**kwargs)

        req = self.request.GET or {}

        # --- Compute Fast Path data --- #
        fp_inbox = fp_models.FastPath.objects.all().order_by('-measurement_start_time')

        # Query dict values come in list form, we're only be concerned by the first values
        req = { key : value[0] for (key, value) in  dict(req).items()}

        # Apply the necessary filters
        since = req.get('since')
        if(since != None and since != ""):
            since = datetime.datetime.strptime(since, '%Y-%m-%d')
            utc_since = utc_aware_date(since, self.request.session['system_tz'])
            fp_inbox = fp_inbox.filter(measurement_start_time__gte=utc_since)

        until = req.get('until')
        if(until != None and until != ""):
            until = datetime.datetime.strptime(until, '%Y-%m-%d')
            utc_until = utc_aware_date(until, self.request.session['system_tz'])
            fp_inbox = fp_inbox.filter(measurement_start_time__lte=utc_until)

        test_name = req.get('testName')
        if (test_name != None and test_name != ""):
            fp_inbox = fp_inbox.filter(test_name=test_name)

        ASN = req.get("asn")
        if (ASN != None and ASN != ""):
            fp_inbox = fp_inbox.filter(probe_asn=ASN)

        inpt = req.get("input")
        if (inpt != None and inpt != ""):
            fp_inbox = fp_inbox.filter(input__contains=inpt)

        anomaly = req.get("anomaly")
        if (anomaly != None and anomaly != ""):
            fp_inbox = fp_inbox.filter(anomaly=anomaly == "true")

        data_ready = req.get("data_ready")

        if data_ready:
            fp_inbox = fp_inbox.filter(data_ready=data_ready)

        current_page = self._paginate(fp_inbox)

        context['inbox_measurements'] = current_page
        context['search_params'] = req
        context['asns'] = AsnModels.ASN.objects.all()

        return context

class GetMeasurement(VSFLoginRequiredMixin, View):
    """
        This view is used to retrieve data for a single measurement
        from the fastpath in Json format.
        Expected GET arguments:
            + tid = fast path measurement id
    """
    def get(self, request, **kwargs):

        tid = self.request.GET or {}
        tid = tid.get('id')
        print('alooooooooooooo')

        if tid != None:
            obj = fp_models.FastPath.objects.get(id=tid)

            print(obj)
            print('-------------------------------')

            data = {
                'anomaly' : obj.anomaly,
                'confirmed' : obj.cofirmed,
                'failure' : obj.failure,
                'input' : obj.input,
                'tid' : obj.tid,
                'measurement_start_time' : obj.measurement_start_time,
                'measurement_url' : obj.measurement_url,
                'probe_asn' : obj.probe_asn,
                'probe_cc' : obj.probe_cc,
                'report_id' : obj.report_id,
                'scores' : obj.scores,
                'test_name' : obj.test_name,
                'report_ready' : obj.report_ready,
                'catch_date' : obj.catch_date.astimezone(CARACAS).strftime("%Y-%m-%d")
            }
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({})

class ListProbes(VSFLoginRequiredMixin, TemplateView):
    # FROZEN
    template_name = "list-probes-templates/list-probes.html"


