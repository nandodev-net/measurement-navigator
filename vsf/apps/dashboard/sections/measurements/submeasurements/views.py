#Django imports
from django.http import request
from django.views.generic           import TemplateView
from django.db.models.expressions   import RawSQL
from django.db.models               import OuterRef, Subquery

#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin
#Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from datetime                                   import datetime, timedelta
# Local imports
from apps.main.sites.models                     import Site
from apps.main.asns                             import models as AsnModels
from apps.main.measurements.submeasurements     import models as SubMeasModels
from apps.main.measurements.flags               import models as FlagModels

# DELETE LATER, DEBUG ONLY @TODO
from vsf.utils                                  import Colors as c

class ListSubMeasurementTemplate(VSFLoginRequiredMixin, TemplateView):
    """
        Base class for submeasurement template listing, it wont work
        if you dont provide a "Submeasurement" object
    """
    SubMeasurement : SubMeasModels.SubMeasurement = None
    def get_context_data(self, **kwargs):
        """
            Returned by context:
                + flags: [{'name': str, 'value' : str}] = List of flag-type objects, each object provides a name (human readable) and a database value
                + sites: [Site] = List of all sites
                + asns : [ASN]  = List of all asn's
                + last_measurement_date: str = Date of last measurement (in a string)
                + prefill : possible default values for table filtering. Supported:
                    - input
                    - since
                    - until
                    - site
                    - anomaly
                    - asn
                    - flag
        """
        # Return the site list so we can perform some
        # filtering based on the site
        sites = Site.objects.all()

        # Get the most recent measurement:
        last_measurement_date = self.SubMeasurement\
                                .objects.all()\
                                .order_by("-measurement__raw_measurement__measurement_start_time")\
                                .values("measurement__raw_measurement__measurement_start_time")\
                                .first()

        #   If there is no measurements, result is going to be none, cover that case.
        if last_measurement_date is None:
            last_measurement_date = "No measurements yet"
        else:
            last_measurement_date = datetime.strftime(
                                                last_measurement_date["measurement__raw_measurement__measurement_start_time"],
                                                "%Y-%m-%d %H:%M:%S"
                                            )

        # Compute flag types
        flag_types = []
        for value, name in FlagModels.Flag.FlagType.choices:
            flag_types.append({'name' : name, 'value':value})

        # Compute prefill 
        get = self.request.GET or {}
        prefill = {}
        inpt = get.get("input")
        if inpt:
            prefill['input'] = inpt

        since = get.get("since")
        prefill['since'] = since or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        until = get.get("until")
        if until:
            prefill['until'] = until

        site = get.get("site")
        if site:
            prefill['site'] = site

        anomaly = get.get("anomaly")
        if anomaly:
            prefill['anomaly'] = anomaly

        asn = get.get("asn")
        if asn:
            prefill['asn'] = asn

        flag = get.get('flag')
        if flag:
            prefill['flag'] = flag

        context =  super().get_context_data()
        context['flags'] = flag_types
        context['sites'] = sites
        context['asns'] = AsnModels.ASN.objects.all()
        context['last_measurement_date'] = last_measurement_date
        context['prefill'] = prefill

        return context
    
class ListSubMeasurementBackend(VSFLoginRequiredMixin, BaseDatatableView):
    """
        Base class for backend listing in submeasurement tables. To use this class you should:
            + Append additional columns to "columns" variable
            + Append additional ordering columns to "order_columns" if needed
            + Set a SubMeasurement class (class inheriting SubMeasurement class) [REQUIRED]
            + Define a prepare_results function                                  [REQUIRED]
            + Override o re-filter filter_queryset method ir order to add new filters if needed                        
    """
    # Columns to be shown
    columns = [
            'measurement__raw_measurement__input',
            'measurement__raw_measurement__measurement_start_time',
            'measurement__raw_measurement__probe_asn',
            'measurement__raw_measurement__probe_cc',
            'site_name',
            'measurement__anomaly',
            'flag__flag'
        ]

    # Columns to be ordered
    order_columns = [
            'measurement__raw_measurement__input',
            'measurement__raw_measurement__measurement_start_time',
            'measurement__raw_measurement__probe_asn',
            'measurement__raw_measurement__probe_cc',
            'site_name',
            'measurement__anomaly',
            'flag__flag'
        ]
    
    # SubMeasurement class to use (class inheriting SubMeasurement)
    SubMeasurement = None

    def get_initial_queryset(self):
        qs = self.SubMeasurement.objects.all()\
                .select_related('measurement', 'flag')\
                .select_related('measurement__raw_measurement')\
                .select_related('measurement__domain')\
                .select_related('measurement__domain__site')
        
        return qs

    def filter_queryset(self, qs):
        get = self.request.GET or {}

        # Get filter data

        input       = get.get('input')
        since       = get.get('since')
        asn         = get.get('asn')
        country     = get.get('country')
        anomaly     = get.get('anomaly')
        until       = get.get('until')
        site        = get.get('site')
        flag        = get.get('flag') 
        if input:
            qs = qs.filter(measurement__raw_measurement__input__contains=input)
        if since:
            qs = qs.filter(measurement__raw_measurement__measurement_start_time__gte=since)
        if asn:
            qs = qs.filter(measurement__raw_measurement__probe_asn=asn)
        if country:
            qs = qs.filter(measurement__raw_measurement__probe_cc=country)
        if until:
            qs = qs.filter(measurement__raw_measurement__measurement_start_time__lte=until)
        if site:
            qs = qs.filter(measurement__domain__site=site)
        if anomaly:
            qs = qs.filter(measurement__anomaly= anomaly.lower() == 'true')
        if flag:
            qs = qs.filter(flag_type=flag)

        return qs


class ListDNSTemplate(ListSubMeasurementTemplate):
    """
        This is the template view that renders the html with the dynamic table
    """
    template_name = "measurements-templates/list-dns.html"
    SubMeasurement = SubMeasModels.DNS
    
    def get_context_data(self, **kwargs):
        """
            Besides of the data provided by 'ListSubMeasurementTemplate' parent class, 
            this class provides additional fields:
                + in prefill, add a new field:
                    - consistency
        """
        context =  super().get_context_data()
        prefill = context['prefill']
        get = self.request.GET or {}
    
        consistency = get.get('consistency')

        if consistency:
            prefill['consistency'] = consistency

        context['prefill'] = prefill
        print(context.keys())
        return context

class ListDNSBackEnd(ListSubMeasurementBackend):
    """
        This is the backend that talks to the template to perform
        the server-side data processing operations for the List DNS view
    """
    columns = ListSubMeasurementBackend.columns + [ 'dns_consistency',
                                                    'jsons__answers',
                                                    'jsons__control_answers',
                                                    'control_resolver_hostname',
                                                    'hostname'
                                                ]
    SubMeasurement = SubMeasModels.DNS

    def filter_queryset(self, qs):
        """
            Besides of the data provided by 'ListSubMeasurementTemplate' parent class, 
            this class provides additional filtering:
                + in prefill, add a new field:
                    - consistency
        """
        get = self.request.GET or {}
        qs = super().filter_queryset(qs)
        print(c.yellow(str(qs)))
        consistency = get.get('consistency')
        if consistency:
            qs = qs.filter(dns_consistency__contains=consistency)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:
            json_data.append({
                'measurement__raw_measurement__measurement_start_time':item.measurement.raw_measurement.measurement_start_time,
                'measurement__raw_measurement__probe_cc':item.measurement.raw_measurement.probe_cc,
                'measurement__raw_measurement__probe_asn':item.measurement.raw_measurement.probe_asn,
                'measurement__raw_measurement__input':item.measurement.raw_measurement.input,
                'measurement__id' : item.measurement.raw_measurement.id,
                'site' : item.measurement.domain.site.id if item.measurement.domain and item.measurement.domain.site else -1,
                'site_name' : item.measurement.domain.site.name if item.measurement.domain and item.measurement.domain.site else "(no site)",
                'measurement__anomaly' : item.measurement.anomaly,
                'jsons__answers' : item.jsons.answers,
                'jsons__control_resolver_answers' : item.jsons.control_resolver_answers,
                'client_resolver' : item.client_resolver,
                'dns_consistency' : item.dns_consistency,
                'flag__flag'      : item.flag_type if item.flag else "no flag"
            })
        return json_data

class ListHTTPTemplate(ListSubMeasurementTemplate):
    """
        This is the front-end view for showing the HTTP submeasurement
        table. Note that this view is coupled to the ListDNSBackEnd view.
    """
    template_name = "measurements-templates/list-http.html"
    SubMeasurement = SubMeasModels.HTTP
    def get_context_data(self, **kwargs):
        """
            Besides of the data provided by 'ListSubMeasurementTemplate' parent class, 
            this class provides additional fields:
                + in prefill, add a new field:
                    - status_code_match
                    - headers_match
                    - body_length_match
                    - body_proportion_min
                    - body_proportion_max
        """
        context =  super().get_context_data()
        get = self.request.GET or {}
        prefill = context['prefill']

        status_code_match = get.get("status_code_match")
        if status_code_match:
            prefill['status_code_match'] = status_code_match

        headers_match = get.get("headers_match")
        if headers_match:
            prefill['headers_match'] = headers_match
        
        body_length_match = get.get("body_length_match")
        if body_length_match:
            prefill['body_length_match'] = body_length_match

        body_proportion_min = get.get("body_proportion_min") or 0
        prefill['body_proportion_min'] = body_proportion_min

        body_proportion_max = get.get("body_proportion_max")
        prefill['body_proportion_max'] = body_proportion_max or 1

        context['prefill'] = prefill
        return context

class ListHTTPBackEnd(ListSubMeasurementBackend):
    """
        This is the back end for the HTTP submeasurement table. The dynamic
        table in "ListHTTPTemplate" talks to this view
    """
    columns = ListSubMeasurementBackend.columns +  ['status_code_match',
                                                    'headers_match',
                                                    'body_length_match',
                                                    'body_proportion'
                                                   ]

    order_columns = ListSubMeasurementBackend.columns+ ['status_code_match',
                                                        'headers_match',
                                                        'body_length_match',
                                                        'body_proportion'
                                                       ]

    SubMeasurement = SubMeasModels.HTTP

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        get = self.request.GET or {}

        body_proportion_min = get.get('body_proportion_min')
        body_proportion_max = get.get('body_proportion_max')
        status_code_match   = get.get('status_code_match')
        headers_match       = get.get('headers_match')
        body_length_match   = get.get('body_length_match')

         # Try to parse float values
        try:
            body_proportion_min = float(body_proportion_min)
        except:
            body_proportion_min = 0

        try:
            body_proportion_max = float(body_proportion_max)
        except:
            body_proportion_max = 1

        if status_code_match:
            qs = qs.filter(status_code_match= status_code_match.lower() == 'true')
        if headers_match:
            qs = qs.filter(headers_match= headers_match.lower() == 'true')
        if body_length_match:
            qs = qs.filter(body_length_match= body_length_match.lower() == 'true')
        # avoid filtering border values since they add no information to the filter
        if body_proportion_max != 1:
            qs = qs.filter(body_proportion__lt=body_proportion_max)
        if body_proportion_min != 0:
            qs = qs.filter(body_proportion__lt=body_proportion_min)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:
            json_data.append({
                'measurement__raw_measurement__measurement_start_time':item.measurement.raw_measurement.measurement_start_time,
                'measurement__raw_measurement__probe_cc':item.measurement.raw_measurement.probe_cc,
                'measurement__raw_measurement__probe_asn':item.measurement.raw_measurement.probe_asn,
                'measurement__raw_measurement__input':item.measurement.raw_measurement.input,
                'measurement__id' : item.measurement.raw_measurement.id,
                'site' : item.measurement.domain.site.id if item.measurement.domain and item.measurement.domain.site else -1,
                'site_name' : item.measurement.domain.site.name if item.measurement.domain and item.measurement.domain.site else "(no site)",
                'measurement__anomaly' : item.measurement.anomaly,
                'flag__flag'           : item.flag_type if item.flag else "no flag",
                'status_code_match' : item.status_code_match,
                'headers_match' : item.headers_match,
                'body_length_match' : item.body_length_match,
                'body_proportion' : item.body_proportion,
            })
        return json_data

class ListTCPTemplate(ListSubMeasurementTemplate):
    """
        This is the front-end view for showing the HTTP submeasurement
        table. Note that this view is coupled to the ListDNSBackEnd view.
    """
    template_name = "measurements-templates/list-tcp.html"
    SubMeasurement = SubMeasModels.TCP
    def get_context_data(self, **kwargs):
        """
            Besides of the data provided by 'ListSubMeasurementTemplate' parent class, 
            this class provides additional fields:
                + in prefill, add a new field:
                    - status_blocked
                    - status_failure
                    - status_success
                    - ip
        """
        context =  super().get_context_data()
        prefill = context['prefill']
        get = self.request.GET or {}
        
        blocked = get.get('status_blocked')
        if blocked:
            prefill['status_blocked'] = blocked
        
        status_failure = get.get('status_failure')
        if status_failure:
            prefill['status_failure'] = status_failure
        
        success = get.get('status_success')
        if success:
            prefill['status_success'] = success
        
        ip = get.get('ip')
        if ip:
            prefill['ip'] = ip
        
        context['prefill'] = prefill
        return context

class ListTCPBackEnd(ListSubMeasurementBackend):
    """
        This is the back end for the HTTP submeasurement table. The dynamic
        table in "ListHTTPTemplate" talks to this view
    """
    columns = ListSubMeasurementBackend.columns +  ['status_blocking',
                                                    'status_failure',
                                                    'status_success',
                                                    'ip'
                                                    ]

    order_columns = ListSubMeasurementBackend.order_columns + [ 'status_blocking',
                                                                'status_failure',
                                                                'status_success',
                                                                'ip'
                                                              ]

    SubMeasurement = SubMeasModels.TCP

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        get = self.request.GET or {}

        status_blocked = get.get('status_blocked')
        status_failure = get.get('status_failure')
        status_success = get.get('status_success')
        ip             = get.get('ip')

        if status_blocked:
            qs = qs.filter(status_blocked= status_blocked.lower() == 'true')
        if status_failure:
            qs = qs.filter(status_failure__contains= status_failure)
        if status_success:
            qs = qs.filter(status_success= status_success.lower() == 'true')
        if ip:
            qs = qs.filter(ip__contains=ip)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:
            json_data.append({
                'measurement__raw_measurement__measurement_start_time':item.measurement.raw_measurement.measurement_start_time,
                'measurement__raw_measurement__probe_cc':item.measurement.raw_measurement.probe_cc,
                'measurement__raw_measurement__probe_asn':item.measurement.raw_measurement.probe_asn,
                'measurement__raw_measurement__input':item.measurement.raw_measurement.input,
                'measurement__id' : item.measurement.raw_measurement.id,
                'site' : item.measurement.domain.site.id if item.measurement.domain and item.measurement.domain.site else -1,
                'site_name' : item.measurement.domain.site.name if item.measurement.domain and item.measurement.domain.site else "(no site)",
                'measurement__anomaly' : item.measurement.anomaly,
                'flag__flag'           : item.flag_type if item.flag else "no flag",
                'status_blocked' : item.status_blocked,
                'status_failure' : item.status_failure or "N/A",
                'status_success' : item.status_success,
                'ip' : item.ip,
            })
        return json_data
