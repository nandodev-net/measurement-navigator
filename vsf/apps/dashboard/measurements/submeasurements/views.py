#Django imports
from django.http import request
from django.views.generic           import TemplateView
from django.db.models               import F, QuerySet, Model
from django.core.cache              import caches

#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin

#Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView

# Python imports
from datetime                                   import datetime, timedelta
from typing                                     import Any, Dict, List, Type, Optional
import hashlib
import json

# Local imports
from apps.main.sites.models                     import Site
from apps.main.asns                             import models as AsnModels
from apps.main.measurements.submeasurements     import models as SubMeasModels
from apps.main.measurements.flags               import models as FlagModels

# DELETE LATER, DEBUG ONLY @TODO
from vsf.utils                                  import Colors as c
from ...utils import *
import viztracer

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
        # last_measurement_date = self.SubMeasurement\
        #                         .objects.all()\
        #                         .order_by("-measurement__raw_measurement__measurement_start_time")\
        #                         .values("measurement__raw_measurement__measurement_start_time")\
        #                         .first()

        #   If there is no measurements, result is going to be none, cover that case.
        # if last_measurement_date is None:
        #     last_measurement_date = "No measurements yet"
        # else:
        #     ##last_measurement_date = utc_aware_date(last_measurement_date["measurement__raw_measurement__measurement_start_time"], self.request.session['system_tz'])
        #     last_measurement_date = datetime.strftime(last_measurement_date["measurement__raw_measurement__measurement_start_time"], "%Y-%m-%d %H:%M:%S")

        # Compute flag types
        flag_types = []
        for value, name in FlagModels.Flag.FlagType.choices:
            flag_types.append(name)

        # Compute prefill 
        get = self.request.GET or {}
        prefill = {}
        inpt = get.get("input")
        if inpt:
            prefill['input'] = inpt

        since = get.get("since")
        prefill['since'] = since or (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')

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
        
        if get != {}:
            flags = get.getlist('flags[]')
            if flags:
                prefill['flags'] = flags

        context =  super().get_context_data()
        context['flags'] = flag_types
        context['sites'] = sites
        context['asns'] = AsnModels.ASN.objects.all()
        # context['last_measurement_date'] = last_measurement_date
        context['prefill'] = prefill
        context['measurement_type'] = 'web_connectivity'

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
            'input',
            'measurement_start_time',
            'probe_asn',
            'probe_cc',
            'site_name',
            'anomaly',
            'flag_type'
        ]

    # Columns to be ordered
    order_columns = [
            'input',
            'measurement_start_time',
            'probe_asn',
            'probe_cc',
            'site_name',
            'anomaly',
            'flag_type'
        ]
    
    # SubMeasurement class to use (class inheriting SubMeasurement)
    SubMeasurement : Optional[Type[Model]]= None

    # how many seconds cache will live before it is deleted
    SECONDS_TO_STORE_CACHE = 60 * 5

    def get_initial_queryset(self):
        assert self.SubMeasurement, "Submeasurement not properly configured"

        qs = self.SubMeasurement.objects.select_related('measurement', 'measurement__raw_measurement').all()
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
        flags        = get.getlist('flags[]') if get != {} else []


        if input:
            qs = qs.filter(input__contains=input)
        if since:
            qs = qs.filter(measurement__raw_measurement__measurement_start_time__gte = since)
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
        if flags:
            flags = [flag.lower() for flag in flags]
            qs = qs.filter(flag_type__in = flags)

        return qs
    
    def prepare_results_no_cache(self, qs : QuerySet) -> List[Dict[str, Any]]:
        raise NotImplementedError("Implement prepare_results_no_cache in your submeasurement backend view in order to fill the datatables table")

    def prepare_results(self, qs : QuerySet) -> List[Dict[str, Any]]:
        """Don't override this unless you want to prevent query caching. This function will search for a cached result of the provided query. you 
        can do:
            ```
            def prepare_results(self, qs):
                self.prepare_results_no_cache(qs)
            ```
        in case you want to avoid caching for this view

        Args:
            qs (QuerySet): Queryset whose result will be cached

        Returns:
            List[Dict[str, Any]]: Prepared results as a list of json-like dicts
        """
        key = self._get_key_from_query(qs)
        fs_cache = caches['filesystem']

        # try to retrieve key from cache
        if key in fs_cache:
            print(c.green("Cache found, using cache"))
            result = fs_cache.get(key)
        else: 
            # If not found, then create it 
            print(c.blue("Cache not found, creating from scratch"))
            result = self.prepare_results_no_cache(qs)
            fs_cache.set(key, result, self.SECONDS_TO_STORE_CACHE)

        return result

    def _get_key_from_query(self, qs : QuerySet) -> str:
        """Generate a sha256 key from a given queryset, so it can be used to cache results for a few minutes

        Args:
            qs (QuerySet): Query in database to cache

        Returns:
            str: sha256 hash for the given query
        """
        query_str = str(qs.query)
        query_hash = hashlib.sha256(bytes(query_str, 'utf-8')).digest()
        return str(query_hash)


class ListDNSTemplate(ListSubMeasurementTemplate):
    """
        This is the template view that renders the html with the dynamic table
    """
    template_name = "measurements/list-dns.html"
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
    
        dns_consistency = get.get('dns_consistency')

        if dns_consistency:
            prefill['dns_consistency'] = dns_consistency

        context['prefill'] = prefill
        return context

class ListDNSBackEnd(ListSubMeasurementBackend):
    """
        This is the backend that talks to the template to perform
        the server-side data processing operations for the List DNS view
    """
    columns = ListSubMeasurementBackend.columns + [ 
        'dns_consistency',
        'jsons__answers',
        'jsons__control_answers',
        'control_resolver_hostname',
        'hostname',
    ]
    
    order_columns = ListSubMeasurementBackend.order_columns + [
        'dns_consistency'
    ]
    SubMeasurement = SubMeasModels.DNS

    def get_initial_queryset(self):
        return super().get_initial_queryset().select_related('jsons')


    def _get_req_key(self) -> str:

        dict_to_hash = {}
        for field in self.get_filter_fields():
            value = dict_to_hash[field] = self.request.GET.get(field, None)
            if isinstance(value, list) and all(isinstance(elem, str) for elem in value):
                value.sort(key=lambda x: x) 

        dict_json = json.dumps(dict_to_hash, sort_keys=True)
        key_hash = hashlib.sha256(bytes(dict_json, 'utf-8')).digest()

        return str(key_hash)

    def filter_queryset(self, qs):
        """
            Besides of the data provided by 'ListSubMeasurementBackend' parent class, 
            this class provides additional filtering:
                + in prefill, add a new field:
                    - consistency
        """
        get = self.request.GET or {}
        qs = super().filter_queryset(qs)
        consistency = get.get('dns_consistency')
        
        if consistency:
            qs = qs.filter(dns_consistency__contains=consistency)

        return qs

    def prepare_results_no_cache(self, qs : QuerySet):
        # prepare list with output column data
        # queryset is already paginated here

        qs = qs.only(
            "measurement_start_time",
            "probe_cc",
            "probe_asn",
            "input",
            "measurement__id",
            "measurement__domain__site__name",
            "anomaly",
            "jsons__answers",
            "jsons__control_resolver_answers",
            "client_resolver",
            "dns_consistency" 
        )
        
        json_data = []
        for item in qs.iterator(chunk_size=100):
            json_data.append({
                'measurement__raw_measurement__measurement_start_time':datetime.strftime(utc_aware_date(item.measurement.raw_measurement.measurement_start_time, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
                'measurement__raw_measurement__probe_cc':item.measurement.raw_measurement.probe_cc,
                'measurement__raw_measurement__probe_asn':item.measurement.raw_measurement.probe_asn,
                'measurement__raw_measurement__input':item.measurement.raw_measurement.input,
                'measurement__id' : item.measurement.id,
                'site' : item.measurement.domain.site.id if item.measurement.domain and item.measurement.domain.site else -1,
                'site_name' : item.measurement.domain.site.name if item.measurement.domain and item.measurement.domain.site else "(no site)",
                'measurement__anomaly' : item.measurement.anomaly,
                'jsons__answers' :  self._get_answers(item.jsons.answers),
                'jsons__control_resolver_answers' : self._get_control_resolver_answers(item.jsons.control_resolver_answers),
                'client_resolver' : item.client_resolver,
                'dns_consistency' : item.dns_consistency,
                'flag_type'       : item.flag_type
            })
        return json_data

    def _get_answers(self, answers : List[dict]) -> dict:
        """
            Get just ipv4/ipv6 field from 'answers' field.
            return a dict {isOk : b, json : dict} where b : bool tells if the provided dict is a json object
            or our processed version with the following format:
            {
                ipv6 : [str],
                ipv4 : [str],
                cname: [str]
            }
            if true, it is a processed version. Otherwise it's just the raw json
        """
        try:
            out = {}

            out['A']  = [answer.get('ipv4')  for answer in answers if answer.get('answer_type')=='A']
            out['AAAA']  = [answer.get('ipv6')  for answer in answers if answer.get('answer_type')=='AAAA']
            out['cname'] = [answer.get('cname') for answer in answers if answer.get('answer_type')=='cname']
            
            if out['A'] or out['AAAA'] or out['cname']: 
                return {'isOk' : True, 'json' : out}
            else:
                return {'isOk' : False, 'json' : answers}

        except:
            return {'isOk' : False, 'json' : answers}

    def _get_control_resolver_answers(self, cr_answers : dict) -> dict:
        """
            Return a dict 
            {
                isOk : bool,
                json : dict
            }

            such that isOk tells if the provided json is our processed version or the raw json, 
            so we can render it different if the processing was ok
        """
        try:
            out = cr_answers['addrs']
            return {'isOk' : True, 'json' : out}
        except:
            return {'isOk' : False, 'json' : cr_answers}

    @staticmethod
    def get_filter_fields() -> List[str]:
        fields = ListSubMeasurementBackend.get_filter_fields()
        fields.append("dns_consistency")
        return fields

class ListHTTPTemplate(ListSubMeasurementTemplate):
    """
        This is the front-end view for showing the HTTP submeasurement
        table. Note that this view is coupled to the ListDNSBackEnd view.
    """
    template_name = "measurements/list-http.html"
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

    def prepare_results_no_cache(self, qs: QuerySet) -> List[Dict[str, Any]]:
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []

        qs = qs.only(
            'measurement_start_time',
            'probe_cc',
            'probe_asn',
            'input',
            'measurement__id',
            'measurement__domain__site__name',
            'anomaly',
            'flag_type',
            'status_code_match',
            'headers_match',
            'body_length_match',
            'body_proportion'
        )

        for item in qs:
            json_data.append({
                'measurement__raw_measurement__measurement_start_time':datetime.strftime(utc_aware_date(item.measurement.raw_measurement.measurement_start_time, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
                'measurement__raw_measurement__probe_cc':item.measurement.raw_measurement.probe_cc,
                'measurement__raw_measurement__probe_asn':item.measurement.raw_measurement.probe_asn,
                'measurement__raw_measurement__input':item.measurement.raw_measurement.input,
                'measurement__id' : item.measurement.id,
                'site' : item.measurement.domain.site.id if item.measurement.domain and item.measurement.domain.site else -1,
                'site_name' : item.measurement.domain.site.name if item.measurement.domain and item.measurement.domain.site else "(no site)",
                'measurement__anomaly' : item.measurement.anomaly,
                'flag_type'           : item.flag_type,
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
    template_name = "measurements/list-tcp.html"
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

    def prepare_results_no_cache(self, qs: QuerySet) -> List[Dict[str, Any]]:
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []

        qs = qs.only(
            'measurement_start_time',
            'probe_cc',
            'probe_asn',
            'input',
            'measurement__id',
            'measurement__domain__site__name',
            'anomaly',
            'flag_type',
            'status_blocked',
            'status_failure',
            'status_success',
            'ip'
        )

        for item in qs:
            json_data.append({
                'measurement__raw_measurement__measurement_start_time':datetime.strftime(utc_aware_date(item.measurement.raw_measurement.measurement_start_time, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
                'measurement__raw_measurement__probe_cc':item.measurement.raw_measurement.probe_cc,
                'measurement__raw_measurement__probe_asn':item.measurement.raw_measurement.probe_asn,
                'measurement__raw_measurement__input':item.measurement.raw_measurement.input,
                'measurement__id' : item.measurement.id,
                'site' : item.measurement.domain.site.id if item.measurement.domain and item.measurement.domain.site else -1,
                'site_name' : item.measurement.domain.site.name if item.measurement.domain and item.measurement.domain.site else "(no site)",
                'measurement__anomaly' : item.measurement.anomaly,
                'flag_type'           : item.flag_type,
                'status_blocked' : item.status_blocked,
                'status_failure' : item.status_failure or "N/A",
                'status_success' : item.status_success,
                'ip' : item.ip,
            })
        return json_data

class ListTorTemplate(ListSubMeasurementTemplate):
    """
        This is the front-end view for showing the TOR submeasurement
        table. 
    """
    template_name = "measurements/list-tor.html"
    SubMeasurement = SubMeasModels.TOR

    def get_context_data(self, **kwargs):

        context =  super().get_context_data()
        prefill = context['prefill']
        get = self.request.GET or {}

        dir_port_accessible = get.get('dir_port_accessible')
        if dir_port_accessible:
            prefill['dir_port_accessible'] = dir_port_accessible
        else:
            prefill['dir_port_accessible'] = 50
        
        obfs4_accessible = get.get('obfs4_accessible')
        if obfs4_accessible:
            prefill['obfs4_accessible'] = obfs4_accessible
        else:
            prefill['obfs4_accessible'] = 50

        or_port_dirauth_accessible = get.get('or_port_dirauth_accessible')
        if or_port_dirauth_accessible:
            prefill['or_port_dirauth_accessible'] = or_port_dirauth_accessible
        else:
            prefill['or_port_dirauth_accessible'] = 50

        context['prefill'] = prefill
        context['measurement_type'] = 'tor'
        return context
    
class ListTORBackEnd(ListSubMeasurementBackend):
    """
        This is the back end for the tor submeasurement table. The dynamic
        table in "ListTORTemplate" talks to this view
    """

    columns = ListSubMeasurementBackend.columns +  [
        'dir_port_total',
        'dir_port_accessible',
        'obfs4_total',
        'obfs4_accessible',
        'or_port_dirauth_total',
        'or_port_dirauth_accessible'
    ]

    order_columns = ListSubMeasurementBackend.order_columns +  [
        'dir_port_total',
        'dir_port_accessible',
        'obfs4_total',
        'obfs4_accessible',
        'or_port_dirauth_total',
        'or_port_dirauth_accessible'
    ]

    SubMeasurement = SubMeasModels.TOR

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        get = self.request.GET or {}

        dir_port_accessible = get.get('dir_port_accessible')
        if dir_port_accessible: dir_port_accessible = int(dir_port_accessible) / 100
        
        obfs4_accessible = get.get('obfs4_accessible')
        if obfs4_accessible: obfs4_accessible = int(obfs4_accessible) / 100
        
        or_port_dirauth_accessible = get.get('or_port_dirauth_accessible')
        if or_port_dirauth_accessible: or_port_dirauth_accessible = int(or_port_dirauth_accessible) / 100

        if dir_port_accessible:
            qs = qs.filter(dir_port_accessible__lte = F('dir_port_total') * dir_port_accessible)
        if obfs4_accessible:
            qs = qs.filter(obfs4_accessible__lte = F('obfs4_total') * obfs4_accessible)
        if or_port_dirauth_accessible:
            print('entro aca')
            print(qs)
            qs = qs.filter(or_port_dirauth_accessible__lte = F('or_port_dirauth_total') * or_port_dirauth_accessible)
            print(qs)
            
        return qs

    def prepare_results_no_cache(self, qs: QuerySet) -> List[Dict[str, Any]]:
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []

        qs = qs.only(
            'measurement_start_time',
            'probe_asn',
            'measurement__id',
            'flag_type',
            'dir_port_total',
            'dir_port_accessible',
            'obfs4_total',
            'obfs4_accessible',
            'or_port_dirauth_total',
            'or_port_dirauth_accessible'
        )
        
        for item in qs:
            json_data.append({
                'measurement__raw_measurement__measurement_start_time':datetime.strftime(utc_aware_date(item.measurement.raw_measurement.measurement_start_time, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
                'measurement__raw_measurement__probe_asn':item.measurement.raw_measurement.probe_asn,
                'measurement__id' : item.measurement.id,
                'dir_port_total' : item.dir_port_total or 0,
                'dir_port_accessible' : item.dir_port_accessible or 0,
                'obfs4_total' : item.obfs4_total or 0,
                'flag_type'   : item.flag_type,
                'obfs4_accessible' : item.obfs4_accessible or 0, 
                'or_port_dirauth_total': item.or_port_dirauth_total,
                'or_port_dirauth_accessible': item.or_port_dirauth_accessible
            })

        return json_data