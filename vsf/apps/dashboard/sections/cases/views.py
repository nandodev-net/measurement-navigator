#Django imports
from django.views.generic           import ListView
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
from django.contrib.messages.views  import SuccessMessageMixin
from django.views.generic.edit      import FormView
#Local imports
from apps.main.cases                import models as CasesModels
from .forms                         import NewCategoryForm



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