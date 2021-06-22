# Django imports
from django.shortcuts               import redirect, HttpResponseRedirect
from django.http                    import HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins     import LoginRequiredMixin
from django.contrib.auth.views      import LoginView
from django.views.generic import  View

def redirect_to_dashboard(request):
    return redirect('dashboard/')

class VSFLoginRequiredMixin(LoginRequiredMixin):
    """
        View mixin required by multiple views around the project
        to ensure Login Required
    """
    login_url = "/dashboard/login/"
    redirect_field_name = "redirect_to"

class VSFLogin(LoginView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.request.session['system_tz'] = "2"
        return context



class TZoneSelectorView(LoginRequiredMixin, View):
    """
        This view handle the tz of the entire app
    """

    def get(self, request, **kwargs):
        """
            this method assign a tz to a session variable
        """
        _tz = self.request.GET or {}
        _tz = _tz.get('tz')
        self.request.session['system_tz'] = str(_tz)
        return JsonResponse({'system_tz': self.request.session['system_tz']})