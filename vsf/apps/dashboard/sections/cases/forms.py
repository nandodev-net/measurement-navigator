# Django imports
from django.forms           import ModelForm

# Local imports
from apps.main.sites.models import Site
from apps.main.cases.models import Category

class NewCategoryForm(ModelForm):
    """
        form to create a new category
    """
    class Meta:
        model = Category
        fields = ['name', 'display_name']


    