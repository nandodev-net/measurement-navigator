# Django imports
from django.shortcuts               import redirect
from django.contrib.auth.mixins     import LoginRequiredMixin
from django.contrib.auth.views      import LoginView

def redirect_to_dashboard(request):
    return redirect('dashboard/')

class VSFLoginRequiredMixin(LoginRequiredMixin):
    """
        View mixin required by multiple views around the project
        to ensure Login Required
    """
    login_url = "login/"
    redirect_field_name = "redirect_to"

class VSFLogin(LoginView):
    redirect_authenticated_user = True