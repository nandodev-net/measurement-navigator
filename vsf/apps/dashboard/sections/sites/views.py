#Django imports
from django.views.generic           import TemplateView
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
from apps.dashboard.views           import VSFListPaginate
# Local imports
from apps.main.sites.forms                      import SiteForm
from apps.main.sites.models                     import URL, Site


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
