# Django imports
from django.forms           import ModelForm

# Local imports
from .models import Site

class SiteForm(ModelForm):
    """
        Form to create a new site
    """
    class Meta:
        model = Site
        fields = ['name', 'description_spa', 'description_eng']