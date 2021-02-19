#Django imports
from django.views.generic           import ListView

#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
from django.contrib.messages.views  import SuccessMessageMixin
from django.views.generic.edit      import FormView

#Local imports
from apps.main.cases.models import Case
from .forms import CaseForm




