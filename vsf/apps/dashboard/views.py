# Django imports
from django.db.models.expressions   import RawSQL
from django.db.models.query         import QuerySet
from django.views.generic.edit      import FormView
from django.core.paginator          import Paginator, Page
from django.db.models               import OuterRef, Subquery
from django.contrib.messages.views  import SuccessMessageMixin
from django.views.generic           import TemplateView, ListView, View, CreateView
from django.http                    import HttpResponse, JsonResponse, HttpResponseBadRequest, Http404

# third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView

# Local imports
from apps.main.sites.forms                      import SiteForm
from apps.main.sites.models                     import URL, Site
from .forms                                     import NewCategoryForm
from apps.main.ooni_fp.fp_tables                import models as fp_models
from apps.main.measurements                     import models as MeasModels
from apps.main.measurements.submeasurements     import models as SubMeasModels
from apps.main.events                           import models as EventModels
from apps.main.cases                            import models as CasesModels
from vsf.views                                  import VSFLoginRequiredMixin, VSFLogin
from vsf.utils                                  import MeasurementXRawMeasurementXSite
from apps.main.measurements.utils               import search_measurement_by_queryset, search_measurement
import json

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
    def _paginate(self, querySet : QuerySet ) -> Page:
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


        return Paginator(querySet, page_size).get_page(page)



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

    def get_context_data(self, **kwargs):
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
            fp_inbox = fp_inbox.filter(measurement_start_time__gte=since)

        until = req.get('until')
        if(until != None and until != ""):
            fp_inbox = fp_inbox.filter(measurement_start_time__lte=until)

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
        print(data_ready)
        if data_ready:
            fp_inbox = fp_inbox.filter(data_ready=data_ready)

        current_page = self._paginate(fp_inbox)

        context['inbox_measurements'] = current_page
        context['search_params'] = req

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

        if tid != None:
            obj = fp_models.FastPath.objects.get(id=tid)

            data = {
                'anomaly' : obj.anomaly,
                'confirmed' : obj.confirmed,
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
                'catch_date' : obj.catch_date
            }
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({})


# --- EVENTS VIEWS --- #
class ListEvents(VSFLoginRequiredMixin, ListView):
    # FROZEN
    """
        View to list all events
    """
    template_name = "events-templates/list-events.html"
    model = EventModels.Event
    context_object_name = 'events'


# --- CASES VIEWS --- #
class ListCases(VSFLoginRequiredMixin, ListView):
    # FROZEN
    """
        View to list all cases
    """
    template_name = "cases-templates/list-cases.html"
    model = CasesModels.Case
    context_object_name = 'cases'


# --- CATEGORIES VIEWS --- #
class ListCategories(VSFLoginRequiredMixin, ListView):
    # FROZEN
    """
        View to list all case categories
    """
    template_name = "cases-templates/list-categories.html"
    model = CasesModels.Category
    context_object_name = "categories"


class NewCategory(SuccessMessageMixin, VSFLoginRequiredMixin, FormView):
    # FROZEN
    """
        View to render a form to create a new category
    """
    template_name = "cases-templates/new-category.html"
    form_class = NewCategoryForm
    success_message = "Category successfully saved"
    success_url = "#"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


# --- MISC VIEWS --- #
class ListMutedInputs(VSFLoginRequiredMixin, ListView):
    # FROZEN
    """
        View to list all current muted inputs
    """
    template_name = "muted-inputs-templates/list-muted-inputs.html"
    model = EventModels.MutedInput
    context_object_name = "muted_inputs"


class ListProbes(VSFLoginRequiredMixin, TemplateView):
    # FROZEN
    template_name = "list-probes-templates/list-probes.html"

# --- SITES VIEWS --- #
class ListSites(VSFLoginRequiredMixin, TemplateView):
    """
        This view is intended to list all the available sites, so you can
        go to a detailed description of each one and delete sites
    """
    template_name = "sites-templates/list-existent-sites.html"

    def get_context_data(self, **kwargs):
        # Return a list of sites sorted by name
        sites = Site.objects.all().order_by('name')

        context = super().get_context_data()

        # Generate the site form
        siteForm = SiteForm()

        # Return the context
        context['site_creation_form']   = siteForm
        context['sites']                = sites

        return context

class ListUrls(VSFLoginRequiredMixin, VSFListPaginate):
    """
        This view Will handle listing and linking between sites
        and urls.
        This view can handle the following arguments for GET requests:
            url_substr : str = a string that should be contained by
                                an url name string

            page : int = Page index to show

            page_size : int = number of entries per page
    """
    template_name = "sites-templates/list-sites-urls.html"

    def get_context_data(self, **kwargs):
        # Return a list of all available urls, a form for creating
        # a new linking between a site and a set of urls, and
        # a list of sites to link with

        # Get current context
        context = super().get_context_data()

        # Get request object
        get = self.request.GET or {}

        # Get search parameters
        url_substr = get.get('url_substr', "")

        # Ask for the urls with their site, or put None if they have no site
        urls = URL.objects.select_related("site")
        if url_substr != None and url_substr != "":
            urls = urls.filter(url__contains=url_substr)

        urls.order_by('url')

        # Apply pagination:
        try:
            current_page = self._paginate(urls)
        except AttributeError:
            return HttpResponseBadRequest()

        # Get all url objects
        urls = [ {  'url'              : url.url,
                    'id'               : url.id,
                    'site_name'        : url.site.name if url.site != None else "(No site)" ,
                    'site_id'          : url.site.id   if url.site != None else -1,
                    'measurement_count':
                        len(url.reports['reports']) if url.reports.get('reports') != None else 0
                } for url in current_page ]

        urls.sort(key=lambda u: u['url'])

        # Generate the site form
        siteForm = SiteForm()

        # ask por every available site sorted by name
        sites = Site.objects.all().order_by('name')

        # Return the context
        context['urls']                 = urls
        context['site_creation_form']   = siteForm
        context['sites']                = sites
        context['urls_paginator']       = current_page
        context['search_params']        = get
        context['url_substr']           = url_substr

        return context

    def post(self, request, *args, **kwargs):
        """
            This function expects the request to have 2 arguments:
            site: A string with the site id to be related to a set of urls
            urls: an array of string, each representing the id of a single
            url

            Every url given by the request will be associated to the given page
            if it exists.

            This view could return an error in the following cases:
                - The given site does not exists
                - Some of the given urls are already added to some site

            This function will return a jsonResponse with the following format:
            response: {
                error: null | Error,     # If something went wrong, An object describing the error, null otherwise
            }
            Error: {
                type: 'invalid_site' | 'url_already_added_to_a_site',
                url: null | String          # The url string that's inducing some error
            }
        """
        post = dict(request.POST)
        site = post.get('site')
        urls = post.get('urls[]')

        # Check the consistensy of the request
        if urls == None or site == None:
            return HttpResponseBadRequest()

        # Query dict returns a list of string, we're concerned just with one site
        site = site[0] if len(site) > 0 else ''

        # Check that the ids are all integers
        try:
            urls = map(lambda urlid : int(urlid), urls)
        except:
            return HttpResponseBadRequest()

        # Try to get the element
        try:
            dbSite = Site.objects.get(id=site)
        except Site.DoesNotExist:
            return JsonResponse(
                {'error':
                        { 'type': 'unvalid_site', 'url' : None }
                })

        # Try to add this site for every url in the given url list
        dbUrls = URL.objects.all().filter(id__in=urls)

        # Check the urls first
        for url in dbUrls:
            if url.site != None:
                return JsonResponse({
                    'error' :
                        {'type': 'url_already_added_to_a_site', 'url':url.url }
                })

        # Add the site to each url:
        for url in dbUrls:
            url.site = dbSite
            url.save()

        return JsonResponse({'error' : None})

class SiteDetailView(VSFLoginRequiredMixin, VSFListPaginate):
    """
        This view provides a detailed view about a site, showing its description and
        urls related. It expects the id of the site to be showed

        Expected GET arguments:
            id = id of the site whose details are to be retrieved
    """
    template_name = "sites-templates/site-details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        id = kwargs.get('id')

        # Check consistency, if the id is not provided or if it's not an int,
        # return a bad request
        try:
            id = int(id)
        except:
            return context

        # Check if the provided site exists
        try:
            site = Site.objects.get(id=id)
        except:
            return context

        # Now that we have the site, find the urls related to this site
        urls = URL.objects.filter(site=site)

        # Paginate the urls
        current_page = self._paginate(urls)

        # Return the current page and the site in the context
        context['site'] = site
        context['urls'] = current_page
        return context


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
                test_types: The list of available test types
                sites: Site objects describing a site by id, name and description
                pre-fill: additional searching values to pre-fill the search parameters
        """
        # Note that the 'choices' member in a textchoice returns a
        # list of pairs [(s1, s2)] where s2 is the human readable (label) of the choice
        # and s1 is the value itself of the choice
        test_types = MeasModels.RawMeasurement.TestTypes.choices
        test_types = list(map(lambda m: {'name':m[1], 'value':m[0]}, test_types))

        # Now the available sites:
        sites = Site.objects.all().values('name', 'description_eng', 'id')

        # Get the pre-fill search fields
        get = self.request.GET or {}
        prefill = {}

        inpt = get.get("input")
        if inpt:
            prefill['input'] = inpt

        since = get.get("since")
        if since:
            prefill['since'] = since

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

        test_name = get.get('test_name')
        if test_name:
            prefill['test_name'] = test_name

        context = super().get_context_data()
        context['test_types'] = test_types
        context['sites'] = sites
        context['prefill'] = prefill
        return context

class ListMeasurementsBackEnd(BaseDatatableView):
    """
        This is the backend view for the ListMeasurementsDataTable view, who
        just renders the template

        List All Measurements based on the following columns:
            * Input
            * TestName
            * ASN
            * Country Code
            * Site

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
            'site_name',
            'anomaly'
        ]

    order_columns = [
            'raw_measurement__input',
            'raw_measurement__test_name',
            'raw_measurement__measurement_start_time',
            'raw_measurement__probe_asn',
            'raw_measurement__probe_cc',
            'site_name',
            'anomaly'
        ]

    def get_initial_queryset(self):
        return MeasurementXRawMeasurementXSite()

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
            json_data.append({
                'raw_measurement__measurement_start_time':item.raw_measurement.measurement_start_time,
                'raw_measurement__probe_cc':item.raw_measurement.probe_cc,
                'raw_measurement__probe_asn':item.raw_measurement.probe_asn,
                'raw_measurement__input':item.raw_measurement.input,
                'raw_measurement__test_name':item.raw_measurement.test_name,
                'id' : item.id,
                'site' : item.site,
                'site_name' : item.site_name or "(no site)",
                'anomaly' : item.anomaly
            })
        return json_data

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

        context =  super().get_context_data()
        context['test_types'] = test_types
        context['sites'] = sites
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
            'dns_consistency',
            'answers',
            'control_answers',
            'control_resolver_hostname',
            'hostname'

        ]

    order_columns = [
            'measurement__raw_measurement__input',
            'measurement__raw_measurement__measurement_start_time',
            'measurement__raw_measurement__probe_asn',
            'measurement__raw_measurement__probe_cc',
            'site_name',
            'measurement__anomaly'
        ]

    def get_initial_queryset(self):
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
                        client_resolver=RawSQL("measurements_rawmeasurement.test_keys->'client_resolver'", ())
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
                'answers' : json.dumps(item.answers,
                                       indent=2,
                                       sort_keys=True,
                                       skipkeys = True,
                                       allow_nan = True),
                'control_resolver_answers' : json.dumps(item.control_resolver_answers,
                                                        indent=2,
                                                        sort_keys=True,
                                                        skipkeys = True,
                                                        allow_nan = True),
                'client_resolver' : item.client_resolver,
                'dns_consistency' : item.dns_consistency,
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

        context =  super().get_context_data()
        context['sites'] = sites
        return context

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
                .select_related('measurement')\
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

        context =  super().get_context_data()
        context['sites'] = sites
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
                .select_related('measurement')\
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
                'status_blocked' : item.status_blocked,
                'status_failure' : item.status_failure or "N/A",
                'status_success' : item.status_success,
                'ip' : item.ip,
            })
        return json_data