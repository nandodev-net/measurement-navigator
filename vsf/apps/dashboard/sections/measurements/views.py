#Django imports
from django.http.response import Http404
from django.views.generic           import TemplateView, DetailView
from apps.main import measurements
from apps.main.measurements import submeasurements
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin
#Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from typing                                     import List
from datetime                                   import datetime, timedelta
import json
#Utils import
from apps.main.measurements.utils               import search_measurement_by_queryset, search_measurement
#Local imports
from apps.main.sites.models                     import Site
from apps.main.asns                             import models as AsnModels
from apps.main.measurements                     import models as MeasModels
from apps.main.measurements.submeasurements     import models as SubMModels
from apps.main.measurements.flags.models                 import Flag


# --- MEASUREMENTS VIEWS --- #

class ListMeasurementsTemplate(VSFLoginRequiredMixin, TemplateView):
    """
        This is the template that just renders the dynamic table listing
        measurements. All the interaction logic is in the DataBack view.

        This view can receive some special input to pre-fill some input search
        fields.
            Possible inputs:
                - input: Measurement input
                - since: Measurement start time lower bound
                - until: Measurement start time upper bound
                - site: site id for every measurement
                - anomaly: true, false, or an empty string
                - test_name: name of the test for all measurements
    """

    template_name = 'measurements-templates/list-measurements.html'

    def get_context_data(self, **kwargs):
        """
            Return in the context:
                + test_types: The list of available test types, each described by dict with 
                the following format:
                    - name : str = human readable name
                    - value : str = actual name in the database
                + sites: Site objects describing a site by id, name and description
                + asns: List of ASN Objects
                + prefill: additional searching values to pre-fill the search parameters:
                    - input
                    - since
                    - until
                    - site
                    - anomaly
                    - asn
                    - test_name
                    
        """
        # Note that the 'choices' member in a textchoice returns a
        # list of pairs [(s1, s2)] where s2 is the human readable (label) of the choice
        # and s1 is the value itself of the choice
        test_types = MeasModels.RawMeasurement.TestTypes.choices
        test_types = list(map(lambda m: {'name':m[1], 'value':m[0]}, test_types))

        # Now the available sites:
        sites = Site.objects.all().values('name', 'description_spa', 'description_eng', 'id')

        # Get the pre-fill search fields and filter results:
        get = self.request.GET or {}
        prefill = {}

        measurements = MeasModels.Measurement.objects.all()\
            .select_related('raw_measurement').select_related('domain').select_related('domain__site')
        
        inpt = get.get("input")

        if inpt:
            prefill['input'] = inpt
            measurements = measurements.filter(raw_measurement__input__contains=inpt)

        since = get.get("since") or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        prefill['since'] = since 
        
        #measurements = measurements.filter(raw_measurement__measurement_start_time__gte=since)

        until = get.get("until")
        if until:
            prefill['until'] = until
            measurements = measurements.filter(raw_measurement__measurement_start_time__lte=until)
        
        site = get.get("site")
        if site:
            prefill['site'] = site
            measurements = measurements.filter(domain__site=site)

        anomaly = get.get("anomaly")
        if anomaly:
            prefill['anomaly'] = anomaly
            measurements = measurements.filter(anomaly=True)

        asn = get.get("asn")
        if asn:
            prefill['asn'] = asn
            measurements = measurements.filter(raw_measurement__probe_asn=asn)

        test_name = get.get('test_name')
        if test_name:
            prefill['test_name'] = test_name
            measurements = measurements.filter(raw_measurement__test_name=test_name)

        # Get most recent measurement:
        last_measurement_date = MeasModels\
                                .Measurement\
                                .objects.all()\
                                .order_by("-raw_measurement__measurement_start_time")\
                                .values("raw_measurement__measurement_start_time")\
                                .first()

        #   If there is no measurements, result is going to be none, cover that case.
        if last_measurement_date is None:
            last_measurement_date = "No measurements yet"
        else:
            last_measurement_date = datetime.strftime(last_measurement_date["raw_measurement__measurement_start_time"], "%Y-%m-%d %H:%M:%S")
        
        context = super().get_context_data()
        context['test_types'] = test_types
        context['sites'] = sites
        context['prefill'] = prefill
        context['asns'] = AsnModels.ASN.objects.all()
        context['last_measurement_date'] = last_measurement_date
        return context

class MeasurementDetails(VSFLoginRequiredMixin, TemplateView):
    """
        Given the uuid "id" for some measurement through a GET request, 
        return a page with the following data passed within context:

            + measurement: The simple measurement object itself
            + submeasurements: A dict object with the following fields:
                - dns  : A list (possibly empty) with dns submeasurements
                - tcp  : A list (possibly empty) with tcp submeasurements
                - http : A list (possibly empty) with http submeasurements
            + test_keys_string : test_keys json object but as string instead of object
            + error : a string specifying an error type
                - id_not_provided  : unable to find an 'id' atribute in the get request
                - not_found        : there's no measurement with the provided id
                - null             : Everything ok
        
    """
    template_name = "measurements-templates/detailed-info-url.html"

    def get_context_data(self, **kwargs):


        # Get the context so far
        context = super().get_context_data()

        # Get the measurement
        # id = kwargs.get('id')
        id = self.request.GET.get('id')
        # Raise 404 if id is not provided
        if id is None:
            context['error'] = 'id_not_provided'
            return context

        try:
            measurement = MeasModels.Measurement.objects.get(id=id)
        except:
            context['error'] = 'not_found'
            return context

        # List the models, so it is easy to change when adding new submeasurement models
        models : List[(SubMModels.SubMeasurement, str)] = [ (SubMModels.DNS, 'dns'),
                                                            (SubMModels.TCP, 'tcp'),
                                                            (SubMModels.HTTP, 'http')
                                                        ]

        # Ask every submeasurement related to this measurement for each type
        context['submeasurements'] = {}
        for (Model, label) in models:
            context['submeasurements'][label] = Model.objects.filter(measurement=measurement)

        #Test-keys in json string format
        context['test_keys_string'] = json.dumps(measurement.raw_measurement.test_keys)

        # Return the context
        context['measurement'] = measurement
        context['error'] = None
        return context

class MeasurementDetailView(DetailView):
    template_name = 'measurements-templates/measurement-detail.html'
    slug_field = 'pk'
    model = MeasModels.RawMeasurement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rawmeasurement'].test_keys = json.dumps(context['rawmeasurement'].test_keys)
        context['rawmeasurement'].annotations = json.dumps(context['rawmeasurement'].annotations)
        context['rawmeasurement'].test_helpers = json.dumps(context['rawmeasurement'].test_helpers)
        print(context['rawmeasurement'].test_keys)
        return context


class ListMeasurementsBackEnd(BaseDatatableView):
    """
        This is the backend view for the ListMeasurementsDataTable view, who
        just renders the template
        This View requires datatables to send server-side
        paginated data to the front, and it's highly coupled
        with its corresponding template.
    """
    columns = [
            'raw_measurement__input',
            'raw_measurement__test_name',
            'raw_measurement__measurement_start_time',
            'raw_measurement__probe_asn',
            'raw_measurement__probe_cc',
            'domain__site__name',
            'anomaly'
        ]

    order_columns = [
            'raw_measurement__input',
            'raw_measurement__test_name',
            'raw_measurement__measurement_start_time',
            'raw_measurement__probe_asn',
            'raw_measurement__probe_cc',
            'domain__site__name',
            'anomaly'
        ]

    def get_initial_queryset(self):
        return MeasModels.Measurement.objects.all()\
                                        .select_related('raw_measurement')\
                                        .select_related('domain')\
                                        .select_related('domain__site')\

    def filter_queryset(self, qs):
        # Get request params
        get = self.request.GET or {}

        ## Ok this is the kind of solution that i don't like

        # Parse the input data
        input       = get.get('input')
        test_name   = get.get('test_name')
        since       = get.get('since')
        ASN         = get.get('asn')
        country     = get.get('country')
        anomaly     = get.get('anomaly')
        until       = get.get('until')
        site        = get.get('site')

        # Get desired measurements
        measurements = search_measurement_by_queryset(
            qs,
            since=since,
            test_name=test_name,
            ASN=ASN,
            input=input,
            country=country,
            until=until,
            site=site,
            anomaly= anomaly.lower() == "true" if anomaly != None else None
        )

        return measurements

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:

            flagsDNS = [dns.flag.flag for dns in item.dns_set.all()]
            flagsHTTP = [http.flag.flag for http in item.http_set.all()]
            flagsTCP = [tcp.flag.flag for tcp in item.tcp_set.all()]
            
            json_data.append({
                'raw_measurement__measurement_start_time':item.raw_measurement.measurement_start_time,
                'raw_measurement__probe_cc':item.raw_measurement.probe_cc,
                'raw_measurement__probe_asn':item.raw_measurement.probe_asn,
                'raw_measurement__input':item.raw_measurement.input,
                'raw_measurement__test_name':item.raw_measurement.test_name,
                'id' : item.id,
                'site' : item.domain.site.id if item.domain and item.domain.site else -1,
                'site_name' : item.domain.site.name if item.domain and item.domain.site else "(no site)",
                'anomaly' : item.anomaly,
                'flags' : {'dns': flagsDNS, 'http': flagsHTTP, 'tcp': flagsTCP}
            })
        return json_data