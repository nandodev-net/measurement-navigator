#Django imports
from django.views.generic           import TemplateView
from django.http                    import HttpResponseBadRequest, JsonResponse
from requests.models                import CONTENT_CHUNK_SIZE
from django_datatables_view.base_datatable_view import BaseDatatableView
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
from apps.dashboard.views           import VSFListPaginate
import json
# Local imports
from apps.main.sites.forms          import SiteForm
from apps.main.sites.models         import Domain, URL, Site, SiteCategory
# Permission imports
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from apps.main.users import decorators


# --- SITES VIEWS --- #

@method_decorator([login_required, decorators.analist_required], name='dispatch')
class ListSites(VSFLoginRequiredMixin, TemplateView):
    """
        This view is intended to list all the available sites, so you can
        go to a detailed description of each one and delete sites
    """
    template_name = "sites/list-existent-sites.html"

    def get_context_data(self, **kwargs):
        """
            Included in context:
                + site_creation_form : form object to create a site
                + sites : all site objects
        """
        # Return a list of sites sorted by name
        sites = Site.objects.values('id', 'name', 'description_spa', 'description_eng', 'category__code').order_by('name')
        siteCategories = SiteCategory.objects.all()
        categories = [cat.code for cat in siteCategories]
        context = super().get_context_data()

        # Generate the site form
        siteForm = SiteForm()

        # Return the context
        context['site_creation_form']   = siteForm
        context['sites']                = sites
        context['siteCategories'] = json.dumps(categories)
        return context

    def post(self, request, *args, **kwargs):
        post = dict(request.POST)

        assotiation = post.get('association')[0]
        assotiation = json.loads(assotiation)
        for element in assotiation:
            element['category']
            element['site']

            try:
                db_site = Site.objects.get(name=element['site'])
            except Site.DoesNotExist:
                return JsonResponse(
                    {'error':
                            { 'type': 'unvalid_site', 'url' : None }
                    }
                )

            try:
                db_category = SiteCategory.objects.get(code=element['category'])
            except SiteCategory.DoesNotExist:
                return JsonResponse(
                    {'error':
                            { 'type': 'unvalid_site', 'url' : None }
                    }
                )

            db_site.category = db_category
            db_site.save()

        return JsonResponse({'error' : None})


class ListDomains(VSFLoginRequiredMixin, VSFListPaginate):
    """
        This view Will handle listing and linking between sites
        and urls.
        This view can handle the following arguments for GET requests:
            domain_substr : str = a string that should be contained by
                                an url name string

            page : int = Page index to show

            page_size : int = number of entries per page

            error : str = 
                | None if everthing went ok
                | missing_arg
    """
    template_name = "sites/list-sites-domains.html"

    def get_context_data(self, **kwargs):
        """
            In context:
                + domains : list of domain dict objects with the following fields:
                    - domain    =  domain name 
                    - id        =  domain id
                    - site_name = site name if this domain is related to a site
                    - site_id   = site id for the site pointed by this domain
                + site_creation_form : a form object for creating sites
                + sites : list with every site object, ordered by name
                + domains_paginator : paginator object used to get current page and so
                + search_params : get request received by this view
                + domain_substr : substring that should be contained by every domain_name listed here
                + error: possible values = 
                    - missing_args : missing arguments in get request
                    - None: everything ok
                                       
        """
        # Return a list of all available domains, a form for creating
        # a new linking between a site and a set of domains, and
        # a list of sites to link with

        MISSING_ARG_ERROR = "missing_args"

        # Get current context
        context = super().get_context_data()

        # Get request object
        get = self.request.GET or {}

        # Get search parameters
        domain_substr = get.get('domain_substr', "")

        # Ask for the urls with their site, or put None if they have no site
        domains = Domain.objects.select_related("site").order_by('domain_name')
        if domain_substr:
            domains = domains.filter(domain_name__contains=domain_substr)

        # Apply pagination:
        try:
            current_page = self._paginate(domains)
        except AttributeError:
            context['error'] = MISSING_ARG_ERROR
            return context

        # Get all url objects
        domains = [ {'domain'          : domain.domain_name,
                    'id'               : domain.id,
                    'site_name'        : domain.site.name if domain.site != None else "(No site)" ,
                    'site_id'          : domain.site.id   if domain.site != None else -1,
                } for domain in domains ]

        domains.sort(key=lambda u: u['domain'])

        # Generate the site form
        siteForm = SiteForm()

        # ask por every available site sorted by name
        sites = Site.objects.all().order_by('name')

        # Return the context
        context['domains']              = domains
        context['site_creation_form']   = siteForm
        context['sites']                = sites
        context['domains_paginator']    = current_page
        context['search_params']        = get
        context['domain_substr']        = domain_substr
        context['error']                = None

        return context

    def post(self, request, *args, **kwargs):
        """
            This function expects the request to have 2 arguments:
            site: A string with the site id to be related to a set of urls
            domains: an array of id, each representing the id of a single
            domain

            Every domain given by the request will be associated to the given site
            if it exists.

            This view could return an error in the following cases:
                - The given site does not exists
                - Some of the given urls are already added to some site

            This function will return a jsonResponse with the following format:
            response: {
                error: null | Error,     # If something went wrong, An object describing the error, null otherwise
            }
            Error: {
                type: 'invalid_site' | 'domain_already_added_to_a_site',
                domain: null | id          # The domain string that's inducing some error
            }
        """
        post = dict(request.POST)
        site = post.get('site')
        domains = post.get('domains[]')

        print(site)
        print('-------------')
        # Check the consistensy of the request
        if domains == None or site == None:
            return HttpResponseBadRequest()



        # Query dict returns a list of string, we're concerned just with one site
        site = site[0] if len(site) > 0 else ''


        # Check that the ids are all integers
        try:
            domains = map(lambda urlid : int(urlid), domains)
        except:
            return HttpResponseBadRequest()

        # Try to get the element
        try:
            db_site = Site.objects.get(id=site)
        except Site.DoesNotExist:
            return JsonResponse(
                    {'error':
                            { 'type': 'unvalid_site', 'url' : None }
                    }
                )

        # Try to add this site for every url in the given url list
        db_domains = Domain.objects.all().filter(id__in=domains)

        # Check the domains first
        for domain in db_domains:
            if domain.site != None:
                return JsonResponse({
                    'error' :
                        {'type': 'domain_already_added_to_a_site', 'domain': domain.domain_name }
                })

        # Add the site to each url:
        for domain in db_domains:
            domain.site = db_site
            domain.save()

        return JsonResponse({'error' : None})

@method_decorator([login_required, decorators.analist_required], name='dispatch')
class SiteDetailView(VSFLoginRequiredMixin, VSFListPaginate):
    """
        This view provides a detailed view about a site, showing its description and
        urls related. It expects the id of the site to be showed

        Expected GET arguments:
            id = id of the site whose details are to be retrieved
        
            
    """
    template_name = "sites/site-details.html"

    def get_context_data(self, **kwargs):
        """
            In Context:
                + site : requested site object
                + domains: list of domain objects ordered by domain_name
                + error = None | id_not_provided | invalid_id
        """
        context = super().get_context_data()

        id = kwargs.get('id')

        # Declare error strings
        ID_NOT_PROVIDED_ERROR = "id_not_provided"
        INVALID_ID = "invalid_id"

        if id is None:
            context['error'] = ID_NOT_PROVIDED_ERROR
            return context

        # Check consistency, if the id is not provided or if it's not an int,
        # return a bad request
        try:
            id = int(id)
        except:
            context['error'] = INVALID_ID
            return context

        # Check if the provided site exists
        try:
            site = Site.objects.get(id=id)
        except:
            context['error'] = INVALID_ID
            return context

        # Now that we have the site, find the urls related to this site
        urls = Domain.objects.filter(site=site).order_by("domain_name")

        # Paginate the urls
        current_page = self._paginate(urls)

        # Return the current page and the site in the context
        context['site'] = site
        context['domains'] = current_page
        return context

@method_decorator([login_required, decorators.analist_required], name='dispatch')
class SitesEndpoint(BaseDatatableView):

    columns = [
        'associated',
        'name'
    ]

    def get_initial_queryset(self):
        return Site.objects.all()

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            json_data.append({
                'associated': item.id,
                'name' : item.name
            })
        return json_data