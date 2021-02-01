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
                                                .select_related('raw_measurement')\
                                                .select_related('domain')\
                                                .select_related('domain__site')
        
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

        measurementsList = []
        #for measure in measurements:
#
        #    measurementDict = {}
        #    flagsDNS, flagsHTTP, flagsTCP = [], [], []
#
        #    dns = SubMModels.DNS.objects.filter(measurement=measure.id)
        #    http = SubMModels.HTTP.objects.filter(measurement=measure.id)
        #    tcp = SubMModels.TCP.objects.filter(measurement=measure.id)
        #    
        #    for detailDNS in dns:
        #        flag = Flag.objects.filter(id = detailDNS.flag_id)
        #        flagsDNS.append(flag[0].flag)
        #    
        #    for detailHTTP in http:
        #        flag = Flag.objects.filter(id = detailHTTP.flag_id)
        #        flagsHTTP.append(flag[0].flag)
#
        #    for detailTCP in tcp:
        #        flag = Flag.objects.filter(id = detailTCP.flag_id)
        #        flagsTCP.append(flag[0].flag)
        #    
        #    rawmeasurement = measure.raw_measurement
        #    measurementDict['id'] = rawmeasurement.id 
        #    measurementDict['anomaly'] = measure.anomaly 
        #    measurementDict['input'] = rawmeasurement.input 
        #    measurementDict['test_type'] = rawmeasurement.test_name 
        #    measurementDict['measurement_start_time'] = rawmeasurement.measurement_start_time 
        #    measurementDict['probe_cc'] = rawmeasurement.probe_cc 
        #    measurementDict['probe_asn'] = rawmeasurement.probe_asn 
        #    measurementDict['site'] = measure.domain.site.name if measure.domain and measure.domain.site else ""
        #    measurementDict['flags_dns'] = flagsDNS 
        #    measurementDict['flags_http'] = flagsHTTP
        #    measurementDict['flags_tcp'] = flagsTCP
#
        #    measurementsList.append(measurementDict)
        
        measurementsList = map(lambda m : {
            "id" : m.id,
            "anomaly" : m.anomaly,
            "input" : m.raw_measurement.input,
            "test_type" : m.raw_measurement.test_name,
            "measurement_start_time" : m.raw_measurement.measurement_start_time,
            "probe_cc" : m.raw_measurement.probe_cc,
            "site" : m.domain.site.name if m.domain and m.domain.site else "",
            'flags_dns' : m.dns_set.all(),
            'flags_http' : m.http_set.all(),
            'flags_tcp' : m.tcp_set.all()
        }, measurements)
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
        context['measurements'] = measurementsList
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
        print(context['rawmeasurement'].id)
        return context
