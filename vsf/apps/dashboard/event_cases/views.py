#Django imports
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, JsonResponse
from django.views.generic           import ListView, View
from django.views.generic.edit import UpdateView, CreateView

#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin, VSFLogin
from django.contrib.messages.views  import SuccessMessageMixin
from django.views.generic.edit      import FormView

#Local imports
from apps.main.cases.models import Case, Category
from apps.main.events.models import Event
from .forms import CaseForm, CaseCreateForm

#Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from datetime                                   import datetime, timedelta


class CasesListView(VSFLoginRequiredMixin, ListView):
    template_name = "cases/list-cases.html"
    queryset = Case.objects.all()

    def get_context_data(self, **kwargs):

        get, prefill = self.request.GET or {}, {}

        categories = Category.objects.all()
        categoryNames = [cat.name for cat in categories]
        events = Event.objects.all()

        fields = [ 
            'title', 'start_date', 'end_date', 'category', 'draft'
        ]

        for field in fields:
            getter = get.get(field)
            prefillAux = getter if getter else ""
            if field == 'start_date' and not prefill:
                prefillAux = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            elif field:
                prefill[field] = prefillAux

        context = super().get_context_data()
        context['prefill'] = prefill
        context['categoryNames'] = categoryNames
        context['events'] = events
        return context
    

    def post(self, request, *args, **kwargs):
        post = request.POST
        post = dict(request.POST)

        # Cleaning the draft data
        draft = post['draft'][0]
        draft = eval(draft.capitalize())

        #Getting Events objects
        events = post['events[]'] if 'events[]' in post.keys() else []
        eventsObject = Event.objects.filter(id__in=events)

        #Getting Category object
        category = Category.objects.filter(name = post['category'][0]).first()
        
        print('HOLA',post['description_eng'][0] )
        try:
            new_case = Case(
                title = post['title'][0],
                description = post['description'][0],
                description_eng = post['description_eng'][0],
                start_date = post['start_date'][0],
                end_date = post['end_date'][0],
                case_type = post['case_type'][0].lower(),
                category = category,
                twitter_search = post['twitter_search'][0],
                draft = draft
            )     
            
            new_case.save()
            new_case.events.set(eventsObject)
            
            return JsonResponse({'error' : None})

        except Exception as e:
            print(e)
            return HttpResponseBadRequest()


class CasesData(BaseDatatableView):
    "Populate the cases datatable and manage its filters"

    columns = [
        'title',
        'start_date',
        'end_date',
        'category',
        'draft'
    ]

    order_columns = [
        'title',
        'start_date',
        'end_date',
        'category',
        'draft'
    ]

    def get_initial_queryset(self):
        return Case.objects.all().select_related('category')

    def filter_queryset(self, qs):

        # Get request params
        get = self.request.GET or {}

        title, start_date, end_date = get.get('title'), get.get('start_date'), get.get('end_date')
        category, draft =  get.get('category'), get.get('draft')

        if title != None and title != "":
            qs = qs.filter(title__contains = title)
        if start_date != None and start_date != "":
            qs = qs.filter(start_date__gte = start_date)
        if end_date != None and end_date != "":
            qs = qs.filter(end_date__lte = end_date)
        if category != None and category != "":
            qs = qs.filter(category__name = category)
        if draft in ['true', 'false']:
            qs = qs.filter(draft = eval(draft.capitalize()))
            pass
        
        return qs

    def prepare_results(self, qs):

        response = []
        for case in qs:
            category = Category.objects.filter(id = case.category_id).get()
            response.append({
                'id': case.id,
                'title': case.title, 
                'start_date': case.start_date, 
                'end_date': case.end_date, 
                'category': category.name, 
                'draft': case.draft
            })

        return response

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




class CaseDetailData(VSFLoginRequiredMixin, View):

    """
        Returns information about a specific case.
        Expected GET Arguments:
            - id: Case id.
    """

    def get(self, request, **kwargs):

        get = self.request.GET or {}
        caseId = get.get('id')

        if caseId != None:
            caseObj = Case.objects.get(id = caseId)
            print(caseObj.events)
            data = {
                "title": caseObj.title,
                "description": caseObj.description,
                "description_eng": caseObj.description_eng,
                "case_type": caseObj.case_type,
                "start_date": caseObj.start_date,
                "end_date": caseObj.end_date,
                "category": caseObj.category.name,
                "draft": caseObj.draft,
                "twitter_search": caseObj.twitter_search,

            }
            
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({})