#Django imports
from django.views.generic           import TemplateView
from django.db.models.expressions   import RawSQL
from django.db.models               import OuterRef, Subquery

#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin
#Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from datetime                                   import datetime
# Local imports
from apps.main.sites.models                     import URL, Site
from apps.main.asns                             import models as AsnModels
from apps.main.measurements                     import models as MeasModels
from apps.main.measurements.submeasurements     import models as SubMeasModels


class ListDNSTemplate(VSFLoginRequiredMixin, TemplateView):
    """
        This is the template view that renders the html with the dynamic table
    """
    template_name = "measurements-templates/list-dns.html"

    def get_context_data(self, **kwargs):
        # Return the site list so we can perform some
        # filtering based on the site

        test_types = MeasModels.RawMeasurement.TestTypes.choices
        test_types = list(map(lambda m: {'name':m[1], 'value':m[0]}, test_types))
        sites = Site.objects.all()

        # Get the most recent measurement:
        last_measurement_date = SubMeasModels\
                                .DNS\
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

        context =  super().get_context_data()
        context['test_types'] = test_types
        context['sites'] = sites
        context['asns'] = AsnModels.ASN.objects.all()
        context['last_measurement_date'] = last_measurement_date
        return context

class ListDNSBackEnd(VSFLoginRequiredMixin, BaseDatatableView):
    """
        This is the backend that talks to the template to perform
        the server-side data processing operations for the List DNS view
        Columns

            * Sitio
            * Dominio
            * fecha
            * ISP
            * Respuesta
            * repsuesta de control
            * Resolver ip
            * Bloqueado por IP?
            * Resultado de bloqueado (medicion general) ? - Evaluar si genera impacto de desempeño
            * Para que sepan, a futuro: Botón para ver medicion completa en un modal
    """
    columns = [
            'measurement__raw_measurement__input',
            'measurement__raw_measurement__measurement_start_time',
            'measurement__raw_measurement__probe_asn',
            'measurement__raw_measurement__probe_cc',
            'site_name',
            'measurement__anomaly',
            'flag__flag'
            'dns_consistency',
            'jsons__answers',
            'jsons__control_answers',
            'control_resolver_hostname',
            'hostname',

        ]

    order_columns = [
            'measurement__raw_measurement__input',
            'measurement__raw_measurement__measurement_start_time',
            'measurement__raw_measurement__probe_asn',
            'measurement__raw_measurement__probe_cc',
            'site_name',
            'measurement__anomaly',
            'flag__flag'
        ]

    def get_initial_queryset(self):
        # alternativa:
        # select dns.id from submeasurements_dns dns join measurements_measurement ms on dns.measurement_id=ms.id join measurements_rawmeasurement rms on ms.raw_measurement_id=rms.id join (select url, sites.name as site_name from sites_url urls left join sites_site sites on urls.site_id=sites.id) as urls on input=urls.url order by rms.measurement_start_time limit 10;
        # Time for this query to end: 189.96 seconds
        # time for the raw version: 1.89 seconds
        import time

        urls = URL\
                .objects\
                .all()\
                .select_related('site')\
                .filter( url=OuterRef('measurement__raw_measurement__input') )

        qs   = SubMeasModels.DNS.objects.all()\
                .select_related('measurement')\
                .select_related('measurement__raw_measurement')\
                .annotate(
                        site=Subquery(urls.values('site')),
                        site_name=Subquery(urls.values('site__name')),
                    )

        return qs

    def filter_queryset(self, qs):

        get = self.request.GET or {}

        # Get filter data

        input       = get.get('input')
        since       = get.get('since')
        ASN         = get.get('asn')
        consistency = get.get('consistency')
        country     = get.get('country')
        anomaly     = get.get('anomaly')
        until       = get.get('until')
        site        = get.get('site')

        if input:
            qs = qs.filter(measurement__raw_measurement__input__contains=input)
        if since:
            qs = qs.filter(measurement__raw_measurement__measurement_start_time__gte=since)
        if ASN:
            qs = qs.filter(measurement__raw_measurement__probe_asn=ASN)
        if country:
            qs = qs.filter(measurement__raw_measurement__probe_cc=country)
        if until:
            qs = qs.filter(measurement__raw_measurement__measurement_start_time__lte=until)
        if consistency:
            qs = qs.filter(dns_consistency__contains=consistency)
        if site:
            qs = qs.filter(site=site)
        if anomaly:
            qs = qs.filter(measurement__anomaly= anomaly.lower() == 'true')

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
                'measurement__id' : item.measurement.id,
                'site' : item.site,
                'site_name' : item.site_name if item.site_name else "(no site)",
                'measurement__anomaly' : item.measurement.anomaly,
                'jsons__answers' : item.jsons.answers,
                'jsons__control_resolver_answers' : item.jsons.control_resolver_answers,
                'client_resolver' : item.client_resolver,
                'dns_consistency' : item.dns_consistency,
                'flag__flag'      : item.flag.flag if item.flag else "no flag"
            })
        return json_data

class ListHTTPTemplate(VSFLoginRequiredMixin, TemplateView):
    """
        This is the front-end view for showing the HTTP submeasurement
        table. Note that this view is coupled to the ListDNSBackEnd view.
    """
    template_name = "measurements-templates/list-http.html"

    def get_context_data(self, **kwargs):
        # Return the site list so we can perform some
        # filtering based on the site

        sites = Site.objects.all()

        # Get the most recent measurement:
        last_measurement_date = SubMeasModels\
                                .HTTP\
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

        context =  super().get_context_data()
        context['sites'] = sites
        context['asns'] = AsnModels.ASN.objects.all()
        context['last_measurement_date'] = last_measurement_date
        return context

def query():
    urls = URL\
            .objects\
            .all()\
            .select_related('site')\
            .filter( url=OuterRef('measurement__raw_measurement__input') )

    qs   = SubMeasModels.DNS.objects.all()\
            .select_related('measurement', 'flag')\
            .select_related('measurement__raw_measurement')\
            .annotate(
                    site=Subquery(urls.values('site')),
                    site_name=Subquery(urls.values('site__name')),
                    client_resolver=RawSQL("measurements_rawmeasurement.test_keys->'client_resolver'", ())
                ).order_by('measurement__raw_measurement__input')[:10j]
    return qs

class ListHTTPBackEnd(VSFLoginRequiredMixin, BaseDatatableView):
    """
        This is the back end for the HTTP submeasurement table. The dynamic
        table in "ListHTTPTemplate" talks to this view
    """
    columns = [
            'measurement__raw_measurement__input',
            'measurement__raw_measurement__measurement_start_time',
            'measurement__raw_measurement__probe_asn',
            'measurement__raw_measurement__probe_cc',
            'site_name',
            'measurement__anomaly',
            'flag__flag'
            'status_code_match',
            'headers_match',
            'body_length_match',
            'body_proportion'
        ]

    order_columns = [
            'measurement__raw_measurement__input',
            'measurement__raw_measurement__measurement_start_time',
            'measurement__raw_measurement__probe_asn',
            'measurement__raw_measurement__probe_cc',
            'site_name',
            'measurement__anomaly',
            'flag__flag'
            'status_code_match',
            'headers_match',
            'body_length_match',
            'body_proportion'
        ]


    def get_initial_queryset(self):
        urls = URL\
                .objects\
                .all()\
                .select_related('site')\
                .filter( url=OuterRef('measurement__raw_measurement__input') )

        qs   = SubMeasModels.HTTP.objects.all()\
                .select_related('measurement','flag')\
                .select_related('measurement__raw_measurement')\
                .annotate(
                        site=Subquery(urls.values('site')),
                        site_name=Subquery(urls.values('site__name'))
                    )
        return qs

    def filter_queryset(self, qs):

        get = self.request.GET or {}

        # Get filter data

        input       = get.get('input')
        since       = get.get('since')
        ASN         = get.get('asn')
        country     = get.get('country')
        anomaly     = get.get('anomaly')
        until       = get.get('until')
        site        = get.get('site')
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

        if input:
            qs = qs.filter(measurement__raw_measurement__input__contains=input)
        if since:
            qs = qs.filter(measurement__raw_measurement__measurement_start_time__gte=since)
        if ASN:
            qs = qs.filter(measurement__raw_measurement__probe_asn=ASN)
        if country:
            qs = qs.filter(measurement__raw_measurement__probe_cc=country)
        if until:
            qs = qs.filter(measurement__raw_measurement__measurement_start_time__lte=until)
        if site:
            qs = qs.filter(site=site)
        if anomaly:
            qs = qs.filter(measurement__anomaly= anomaly.lower() == 'true')
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
                'measurement__id' : item.measurement.id,
                'site' : item.site,
                'site_name' : item.site_name if item.site_name else "(no site)",
                'measurement__anomaly' : item.measurement.anomaly,
                'flag__flag'           : item.flag.flag if item.flag else "no flag",
                'status_code_match' : item.status_code_match,
                'headers_match' : item.headers_match,
                'body_length_match' : item.body_length_match,
                'body_proportion' : item.body_proportion,
            })
        return json_data

class ListTCPTemplate(VSFLoginRequiredMixin, TemplateView):
    """
        This is the front-end view for showing the HTTP submeasurement
        table. Note that this view is coupled to the ListDNSBackEnd view.
    """
    template_name = "measurements-templates/list-tcp.html"
    def get_context_data(self, **kwargs):
        # Return the site list so we can perform some
        # filtering based on the site

        sites = Site.objects.all()

        # Get the most recent measurement:
        last_measurement_date = SubMeasModels\
                                .TCP\
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

        context =  super().get_context_data()
        context['sites'] = sites
        context['asns'] = AsnModels.ASN.objects.all()
        context['last_measurement_date'] = last_measurement_date
        return context

class ListTCPBackEnd(VSFLoginRequiredMixin, BaseDatatableView):
    """
        This is the back end for the HTTP submeasurement table. The dynamic
        table in "ListHTTPTemplate" talks to this view
    """
    columns = [
            'measurement__raw_measurement__input',
            'measurement__raw_measurement__measurement_start_time',
            'measurement__raw_measurement__probe_asn',
            'measurement__raw_measurement__probe_cc',
            'site_name',
            'measurement__anomaly',
            'flag__flag'
            'status_blocking',
            'status_failure',
            'status_success',
            'ip'
        ]

    order_columns = [
            'measurement__raw_measurement__input',
            'measurement__raw_measurement__measurement_start_time',
            'measurement__raw_measurement__probe_asn',
            'measurement__raw_measurement__probe_cc',
            'site_name',
            'measurement__anomaly',
            'flag__flag',
            'status_blocking',
            'status_failure',
            'status_success',
            'ip'
        ]

    def get_initial_queryset(self):
        urls = URL\
                .objects\
                .all()\
                .select_related('site')\
                .filter( url=OuterRef('measurement__raw_measurement__input') )

        qs   = SubMeasModels.TCP.objects.all()\
                .select_related('measurement', 'flag')\
                .select_related('measurement__raw_measurement')\
                .annotate(
                        site=Subquery(urls.values('site')),
                        site_name=Subquery(urls.values('site__name'))
                    )
        return qs

    def filter_queryset(self, qs):

        get = self.request.GET or {}

        # Get filter data

        input       = get.get('input')
        since       = get.get('since')
        ASN         = get.get('asn')
        country     = get.get('country')
        anomaly     = get.get('anomaly')
        until       = get.get('until')
        site        = get.get('site')
        status_blocked = get.get('status_blocked')
        status_failure = get.get('status_failure')
        status_success = get.get('status_success')
        ip             = get.get('ip')

        if input:
            qs = qs.filter(measurement__raw_measurement__input__contains=input)
        if since:
            qs = qs.filter(measurement__raw_measurement__measurement_start_time__gte=since)
        if ASN:
            qs = qs.filter(measurement__raw_measurement__probe_asn=ASN)
        if country:
            qs = qs.filter(measurement__raw_measurement__probe_cc=country)
        if until:
            qs = qs.filter(measurement__raw_measurement__measurement_start_time__lte=until)
        if site:
            qs = qs.filter(site=site)
        if anomaly:
            qs = qs.filter(measurement__anomaly= anomaly.lower() == 'true')
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
                'measurement__id' : item.measurement.id,
                'site' : item.site,
                'site_name' : item.site_name if item.site_name else "(no site)",
                'measurement__anomaly' : item.measurement.anomaly,
                'flag__flag'           : item.flag.flag if item.flag else "no flag",
                'status_blocked' : item.status_blocked,
                'status_failure' : item.status_failure or "N/A",
                'status_success' : item.status_success,
                'ip' : item.ip,
            })
        return json_data