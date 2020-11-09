# Django imports
from django.shortcuts       import render
from django.views.generic   import View, CreateView
from django.http            import JsonResponse, HttpResponseBadRequest, Http404, HttpResponseGone, HttpResponse

# Local imports
from vsf.views              import VSFLoginRequiredMixin
from .models                import Site, URL

# Create your views here.
class DeleteSiteView(VSFLoginRequiredMixin, View):
    """
        This View expects a post request with the id of the site
        to delete.
    """
    def get(self, request, *args, **kwargs):
        return HttpResponseBadRequest()

    def post(self, request, *args, **kwargs):
        """
            Try to delete a measurement given its ID.
            This function will return a json like object:
            {
                'error': null | 'unvalid_id' 
            }
        """
        post = request.POST
        post = post if post != None else {}

        postId = post.get('id')

        if postId == None or postId == "":
            return HttpResponseBadRequest()

        try:
            mes = Site.objects.get(id=postId)
        except:
            return JsonResponse({"error" : 'unvalid_id'})

        mes.delete()

        return JsonResponse({"error":None})

        

class CreateSiteView(VSFLoginRequiredMixin, CreateView):
    """
        This view is intended to create a new Site based on a post request
        with the site name and description. Its post request expects the following
        fields in the request
            'name' : string         # Unique name for this site
            'description' : string  # Description for this site

        After the request is processed, a json is returned with the error information.
        The possible responses:
        {
            'error' : null | 'unvalid_fields'# A string specifying type of error, or null if no errors
        }
    """
    fields = ['name', 'description']
    model  = Site

    def form_invalid(self, form):
        return JsonResponse({'error':'unvalid_fields'})

    def form_valid(self, form):
        form.save()
        return JsonResponse({'error':None})

class RemoveUrlFromSite(VSFLoginRequiredMixin, View):
    """
        This view will receive a post request to remove an url from a site.
        post input:
        {
            'url': url whose site will be set to null
        }
    """

    def get(self, request, *args, **kwargs):
        return HttpResponseBadRequest()

    def post(self, request, *args, **kwargs):
        # Get post request data
        post = request.POST
        post = post if post != None else {}

        url = post.get('url')
        # Check consistency
        if url == None or url == "" :
            return HttpResponseBadRequest()

        # Check if the url is in the database
        try:
            url_object = URL.objects.get(url=url)
        except URL.DoesNotExist:
            return Http404()

        # Reset site object
        url_object.site = None
        url_object.save()

        # Everything ok
        return HttpResponse(status=202)
