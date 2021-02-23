#Django imports
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic           import ListView
from django.views.generic.edit import UpdateView, CreateView

#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
from django.contrib.messages.views  import SuccessMessageMixin
from django.views.generic.edit      import FormView

#Local imports
from apps.main.cases.models import Case, Category
from .forms import CaseForm, CaseCreateForm


class CasesListView(VSFLoginRequiredMixin, ListView):
    template_name = "cases/list-cases.html"
    queryset = Case.objects.all()



class CaseCreateView(VSFLoginRequiredMixin, CreateView):
    model = Case
    queryset = Case.objects.all()
    form_class = CaseCreateForm
    template_name = "cases/create-case.html"
    success_url = "/dashboard/cases/"

    def get_context_data(self, **kwargs):

        context = super(CaseCreateView, self).get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):

        self.object = None
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        
        self.object = Case(

            title = form.cleaned_data['title'],
            case_type = form.cleaned_data['case_type'],
            start_date = form.cleaned_data['start_date'],
            end_date = form.cleaned_data['end_date'],
            category = form.cleaned_data['category'],
            description = form.cleaned_data['description'],
        )        
        self.object.save()
        return HttpResponseRedirect("/dashboard/cases/")

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                form=form,
            )
        )



class CaseCreateModalView(VSFLoginRequiredMixin, CreateView):
    model = Case
    queryset = Case.objects.all()
    form_class = CaseCreateForm
    template_name = "cases/create-case-form.html"
    success_url = "/dashboard/cases/"

    def get_context_data(self, **kwargs):

        context = super(CaseCreateModalView, self).get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):

        self.object = None
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        
        self.object = Case(

            title = form.cleaned_data['title'],
            case_type = form.cleaned_data['case_type'],
            start_date = form.cleaned_data['start_date'],
            end_date = form.cleaned_data['end_date'],
            category = form.cleaned_data['category'],
            description = form.cleaned_data['description'],
        )        
        self.object.save()
        return HttpResponseRedirect("/dashboard/cases/")

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                form=form,
            )
        )




