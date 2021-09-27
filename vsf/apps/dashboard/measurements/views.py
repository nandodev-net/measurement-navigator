#Django imports
from django.db.models.query         import QuerySet
from django.http import  JsonResponse
from django.db.models               import Subquery, OuterRef
from django.http.response           import Http404
from django.core                    import serializers
from django.views.generic           import TemplateView, DetailView, View
from apps.main                      import measurements
from apps.main.measurements         import submeasurements
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin
#Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from typing                                     import List
from datetime                                   import date, datetime, timedelta
import json
#Utils import
from apps.main.measurements.utils               import search_measurement_by_queryset, _filter_by_flag_no_ok
#Local imports
from apps.main.sites.models                     import Site
from apps.main.asns                             import models as AsnModels
from apps.main.measurements                     import models as MeasModels
from apps.main.measurements.submeasurements     import models as SubMModels
from ..utils import *
import logging

logger = logging.getLogger(__name__)

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

    template_name = 'measurements/list-measurements.html'

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

        since = get.get("since") or (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
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
        
        flags_list = [ 'DNS', 'HTTP', 'TCP' ]
        if get != {}:
            flags = get.getlist('flags[]')
            if flags:
                prefill['flags'] = flags
                measurements = _filter_by_flag_no_ok(measurements, flags)

        measurements.only(
            "raw_measurement__measurement_start_time",
            "raw_measurmenet__test_name",
            "raw_measurement__input",
            "raw_measurement__probe_cc",
            "id",
            "anomaly",
            "site",
            "site__name",
            "flags"
        )

        # Get most recent measurement:
        # last_measurement_date = MeasModels\
        #                         .Measurement\
        #                         .objects.all()\
        #                         .order_by("-raw_measurement__measurement_start_time")\
        #                         .values("raw_measurement__measurement_start_time")\
        #                         .first()
                                

        #   If there is no measurements, result is going to be none, cover that case.
        # if last_measurement_date is None:
        #     last_measurement_date = "No measurements yet"
        # else:
        #     last_measurement_date = utc_aware_date(last_measurement_date["raw_measurement__measurement_start_time"], self.request.session['system_tz'])
        #     last_measurement_date = datetime.strftime(last_measurement_date, "%Y-%m-%d %H:%M:%S")
            
        
        context = super().get_context_data()
        context['test_types'] = test_types
        context['sites'] = sites
        context['prefill'] = prefill
        context['flags'] = flags_list
        context['asns'] = AsnModels.ASN.objects.all()
        # context['last_measurement_date'] = last_measurement_date
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
    template_name = "measurements/detailed-info-url.html"

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

class MeasurementDetailView(VSFLoginRequiredMixin, DetailView):
    template_name = 'measurements/measurement-detail.html'
    slug_field = 'pk'
    model = MeasModels.Measurement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        measurement = context['measurement']

        events = []
        for subm in measurement.dns_list.all(): 
            if subm.event: events.append(subm.event) 
        for subm in measurement.http_list.all(): 
            if subm.event: events.append(subm.event) 
        for subm in measurement.tcp_list.all(): 
            if subm.event: events.append(subm.event) 

        flagsDNS = [subm.flag_type for subm in measurement.dns_list.all()]
        flagsHTTP = [subm.flag_type for subm in measurement.http_list.all()]
        flagsTCP = [subm.flag_type for subm in measurement.tcp_list.all()]

        context['rawmeasurement'] = measurement.raw_measurement
        context['rawmeasurement'].test_keys = measurement.raw_measurement.test_keys
        context['rawmeasurement'].test_helpers = json.dumps(measurement.raw_measurement.test_helpers)
        context['rawmeasurement'].flags = {'dns': flagsDNS, 'http': flagsHTTP, 'tcp': flagsTCP}
        context['events'] = events 
        
        if measurement.raw_measurement.test_name == 'web_connectivity':
            context['rawmeasurement'].hasTcpConnections = len(measurement.raw_measurement.test_keys['tcp_connect']) > 0
            context['rawmeasurement'].platform = measurement.raw_measurement.annotations['platform']
            context['rawmeasurement'].engine = measurement.raw_measurement.annotations['engine_name'] + ' (' + measurement.raw_measurement.annotations['engine_version'] + ')'
            context['rawmeasurement'].hasHttpRequests = len(measurement.raw_measurement.test_keys['requests']) > 0            
            context['rawmeasurement'].annotations = json.dumps(measurement.raw_measurement.annotations)
            context['rawmeasurement'].urlFlag = '/static/img/flags/' + measurement.raw_measurement.probe_cc.lower() + '.svg'
            context['rawmeasurement'].rawjson = serializers.serialize('json', [measurement.raw_measurement])

            tcp_connections = []
            for connection in measurement.raw_measurement.test_keys['tcp_connect']:
                aux = {
                    'ip': connection['ip'],
                    'status': connection['status'],

                }
                
                for key, value in measurement.raw_measurement.test_keys['control']['tcp_connect'].items():
                    if connection['ip'] in key.lower():
                        aux['control_status'] = value['status']
                        aux['control_failure'] = value['failure']

                tcp_connections.append(aux)
            context['rawmeasurement'].tcp_connections = tcp_connections
            
        return context


class ListMeasurementsBackEnd(VSFLoginRequiredMixin, BaseDatatableView):
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
            'anomaly',
        ]

    order_columns = [
            'raw_measurement__input',
            'raw_measurement__test_name',
            'raw_measurement__measurement_start_time',
            'raw_measurement__probe_asn',
            'raw_measurement__probe_cc',
            'domain__site__name',
            'anomaly',
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
        flags        = get.getlist('flags[]') if get != {} else []
        

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
            anomaly= anomaly.lower() == "true" if anomaly else None,
            flags=flags
        )

        return measurements

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        ok_flag = SubMModels.SubMeasurement.FlagType.OK

        qs = qs.only(
                'raw_measurement__measurement_start_time',
                "raw_measurement__probe_cc",
                "raw_measurement__probe_asn",
                "raw_measurement__input",
                "raw_measurement__test_name",
                "id",
                "domain",
                "domain__site__name"
            )

        for item in qs:
            flagsDNS  = any(subm.flag_type != ok_flag for subm in item.dns_list.all())
            flagsHTTP = any(subm.flag_type != ok_flag for subm in item.http_list.all())
            flagsTCP  = any(subm.flag_type != ok_flag for subm in item.tcp_list.all())

            json_data.append({
                'raw_measurement__measurement_start_time':datetime.strftime(utc_aware_date(item.raw_measurement.measurement_start_time, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
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


class MeasurementCounter(VSFLoginRequiredMixin, View): 

    def get(self, request, **kwargs):
        get = self.request.GET or {}
        
        measurements = MeasModels.Measurement.objects.all()

        #--------------- Starting Filter -----------------#

        # -- Input Filter
        input = get.get("input")
        if input:
            measurements = measurements.filter(raw_measurement__input__contains=input)
        # -- Start Date Filter
        since = get.get("since") or (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')        
        # measurements = measurements.filter(raw_measurement__measurement_start_time__gte=since)
        # -- End Date Filter
        until = get.get("until")
        if until:
            measurements = measurements.filter(raw_measurement__measurement_start_time__lte=until)
        # -- Site Filter
        site = get.get("site")
        if site: measurements = measurements.filter(domain__site=site)
        # -- Anomaly Filter
        anomaly = get.get("anomaly")
        if anomaly: measurements = measurements.filter(anomaly=True)
        # -- ASN Filter
        asn = get.get("asn")
        if asn: measurements = measurements.filter(raw_measurement__probe_asn=asn)
        
        # -- Measurement Type Filter
        measurement_type = get.get("measurement_type")
        if measurement_type == 'dns':
            measurements = SubMModels.DNS.objects.filter(measurement__in = measurements)
        elif measurement_type == 'http':
           measurements = SubMModels.HTTP.objects.filter(measurement__in = measurements)
        elif measurement_type == 'tcp':        
            measurements = SubMModels.TCP.objects.filter(measurement__in = measurements)

        today = datetime.now()
        delta = today - datetime.strptime(since, "%Y-%m-%d")

        # Dates Array
        dates_array = []
        # Measurement Quantity by Flag
        ok_qtty = []
        soft_qtty = []
        hard_qtty = []
        muted_qtty = []
        manual_qtty = []
        for index in range(1, delta.days + 1):
            aux = datetime.strptime(since, "%Y-%m-%d") + timedelta(days=index)
            dates_array.append(aux.strftime("%Y-%m-%d"))
            x = measurements.filter(measurement_start_time__date = aux.strftime("%Y-%m-%d"))

            ok = x.filter(flag_type=SubMModels.SubMeasurement.FlagType.OK).count()
            ok_qtty.append(ok)

            print(ok)
            soft = x.filter(flag_type=SubMModels.SubMeasurement.FlagType.SOFT).count()
            soft_qtty.append(soft)

            hard = x.filter(flag_type=SubMModels.SubMeasurement.FlagType.HARD).count()
            hard_qtty.append(hard)

            muted = x.filter(flag_type=SubMModels.SubMeasurement.FlagType.MUTED).count()
            muted_qtty.append(muted)

            manual = x.filter(flag_type=SubMModels.SubMeasurement.FlagType.MANUAL).count()
            manual_qtty.append(manual)

        return JsonResponse({
            'dates': dates_array,
            'ok': ok_qtty,
            'soft': soft_qtty,
            'hard': hard_qtty,
            'muted': muted_qtty,
            'manual': manual_qtty,
        }, safe=False)