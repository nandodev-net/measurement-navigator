#Django imports
from django.http                import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, JsonResponse
from django.views.generic       import ListView, View, DetailView
from django.views.generic.edit  import UpdateView, CreateView
from django.shortcuts           import get_object_or_404, redirect, render

#Inheritance imports
from vsf.views                  import VSFLoginRequiredMixin, VSFLogin

#Local imports
from apps.main.cases.models     import Case, Category
from apps.main.events.models    import Event
from .forms import CaseCreateForm
from ..utils import *

#Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from datetime                                   import datetime, timedelta
from ..utils import *
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.main.asns.models          import ASN


class CasesListView(VSFLoginRequiredMixin, ListView):
    template_name = "cases/list-cases.html"
    queryset = Case.objects.all()

    def get_context_data(self, **kwargs):

        get, prefill = self.request.GET or {}, {}
        print(get)
        categories = Category.objects.all()
        categoryNames = [cat.name for cat in categories]
        fields = [ 
            'title', 'start_date', 'end_date', 'category', 'is_active', 'published'
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
        return context
    

    def post(self, request, *args, **kwargs):
        post = request.POST
        post = dict(request.POST)

        # Cleaning the published data
        published = post['published'][0]
        published = eval(published.capitalize())

        #Getting Events objects
        events = post['events[]'] if 'events[]' in post.keys() else []
        eventsObject = Event.objects.filter(id__in=events)

        #Getting Category object
        category = Category.objects.filter(name = post['category'][0]).first()
 
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
                published = published
            )     
            
            new_case.save()
            new_case.events.set(eventsObject)
            
            return JsonResponse({'error' : None})

        except Exception as e:
            return HttpResponseBadRequest()

class CasesData(VSFLoginRequiredMixin, BaseDatatableView):
    "Populate the cases datatable and manage its filters"

    columns = [
        'title',
        'start_date',
        'end_date',
        'category',
        'published',
        'is_active'
    ]

    order_columns = [
        'title',
        'start_date',
        'end_date',
        'category',
        'published',
        'is_active'
    ]

    def get_initial_queryset(self):
        return Case.objects.all().select_related('category')

    def filter_queryset(self, qs):

        # Get request params
        get = self.request.GET or {}

        title, start_date, end_date = get.get('title'), get.get('start_date'), get.get('end_date')
        category, published, is_active =  get.get('category'), get.get('published'), get.get('is_active')


        if title != None and title != "":
            qs = qs.filter(title__contains = title)

        if start_date != None and start_date != "":
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            utc_start_time = utc_aware_date(start_date, self.request.session['system_tz'])
            qs = qs.filter(start_date__gte = utc_start_time)

        if end_date != None and end_date != "":
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            utc_end_date = utc_aware_date(end_date, self.request.session['system_tz'])
            qs = qs.filter(end_date__lte = utc_end_date)

        if category != None and category != "":
            qs = qs.filter(category__name = category)

        if published in ['true', 'false']:
            qs = qs.filter(published = eval(published.capitalize()))
        
        if is_active in ['true', 'false']:
            qs = qs.filter(is_active = eval(is_active.capitalize()))
        
        return qs

    def prepare_results(self, qs):

        response = []
        for case in qs:
            category = Category.objects.filter(id = case.category_id).get()

            response.append({
                'id': case.id,
                'title': case.title, 
                'start_date': case.get_start_date(), 
                'end_date': case.get_end_date(), 
                'category': category.name, 
                'published': case.published,
                'is_active': case.is_active
            })

        return response


@method_decorator(csrf_exempt, name='dispatch')
class CaseCreateView(VSFLoginRequiredMixin, CreateView):
    model = Case
    queryset = Case.objects.all()
    form_class = CaseCreateForm
    template_name = "cases/create-case.html"
    success_url = "/dashboard/cases/"

    def get_context_data(self, **kwargs):
        
        context = super(CaseCreateView, self).get_context_data(**kwargs)
        categories = Category.objects.all()
        categoryNames = [cat.name for cat in categories]
        context['categoryNames'] = categoryNames
        issueTypes = Event.IssueType.choices
        issueTypes = list(map(lambda m: {'name': m[1].upper(), 'value': m[0]}, issueTypes))
        context['event_filter'] = {
            'asns': ASN.objects.all(),
            'issues': issueTypes,
            'start_time': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        }
        return context

    def post(self, request, *args, **kwargs):

        post = request.POST
        post = dict(request.POST)

        #Getting Events objects
        events = post['events[]'] if 'events[]' in post.keys() else []
        eventsObject = Event.objects.filter(id__in=events)

        published = eval(post['published'][0].capitalize())
        is_active = False
        manual_is_active = eval(post['activate'][0].capitalize())
        if manual_is_active: is_active = True


        
        start_date_automatic, end_date_automatic = None, None
        if 'events[]' in post.keys():
            # Filtering the early and oldest date in the selected events.
            ordered_by_start_date = eventsObject.order_by('start_date')
            ordered_by_end_date = eventsObject.order_by('end_date')
            start_date_automatic = ordered_by_start_date.first().start_date.replace(tzinfo=None) or None
            end_date_automatic = ordered_by_end_date.last().end_date.replace(tzinfo=None) or None
            if end_date_automatic:
                if end_date_automatic > datetime.now(): is_active = True

        #Getting Category object
        category = Category.objects.filter(name = post['category'][0]).first()
        

        start_date_manual, end_date_manual = None, None 
        if post['start_date'][0] != '':
            start_date_manual = datetime.strptime(post['start_date'][0], '%Y-%m-%d %H:%M')
        if post['end_date'][0] != '':
            end_date_manual = datetime.strptime(post['end_date'][0], '%Y-%m-%d %H:%M')
            # If the manual end date selected is greater than today, then the case
            # will be active. 
            if end_date_manual > datetime.now(): is_active = True
        if start_date_manual and end_date_manual and start_date_manual > end_date_manual:
            return JsonResponse({'error' : 'The end date selected must be greater than the start date selected'})



        # Deciding which date put in the main dates fields.
        start_date, end_date = start_date_manual, end_date_manual 
        if 'events[]' in post.keys() and not start_date and not end_date:
            start_date, end_date = start_date_automatic, end_date_automatic 

        try:
            new_case = Case(
                title = post['title'][0],
                title_eng = post['title_eng'][0],
                description = post['description'][0],
                description_eng = post['description_eng'][0],
                start_date = start_date,
                start_date_manual = start_date_manual,
                start_date_automatic = start_date_automatic,
                end_date = end_date,
                end_date_manual = end_date_manual,
                end_date_automatic = end_date_automatic,
                case_type = post['case_type'][0].lower(),
                category = category,
                twitter_search = post['twitter_search'][0],
                published = published,
                is_active = is_active,
                manual_is_active = manual_is_active
            )
            new_case.save()
            new_case.events.set(eventsObject)
            
            return JsonResponse({'error' : None})

        except Exception as e:
            return JsonResponse({'error' : e})
            # return HttpResponseBadRequest()

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
            title_eng = form.cleaned_data['title_eng'],
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
            relatedEvents = caseObj.events.all()

            events = [{
                'id': event.id,
                'identification': event.identification,
                'confirmed': event.confirmed,
                'start_date': datetime.strftime(utc_aware_date(event.start_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
                'end_date': datetime.strftime(utc_aware_date(event.end_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
                'public_evidence': event.public_evidence,
                'private_evidence': event.private_evidence,
                'issue_type': event.issue_type,
                'it_continues': event.it_continues,
                'domain': event.domain.domain_name,
                'asn': event.asn.asn,
                'closed': event.closed

            } for event in relatedEvents]
            
            data = {
                "title": caseObj.title,
                "title_eng": caseObj.title_eng,
                "description": caseObj.description,
                "description_eng": caseObj.description_eng,
                "case_type": caseObj.case_type,
                'start_date': datetime.strftime(utc_aware_date(caseObj.start_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S") if caseObj.start_date else None,
                'end_date': datetime.strftime(utc_aware_date(caseObj.end_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S") if caseObj.end_date else None,
                'start_date_manual': caseObj.start_date_manual,
                'end_date_manual': caseObj.end_date_manual,
                "category": caseObj.category.name,
                "published": caseObj.published,
                "twitter_search": caseObj.twitter_search,
                "events": events,
                "is_it_continues": caseObj.is_active

            }
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({})

class CaseDetailView(VSFLoginRequiredMixin, DetailView):
    template_name = 'cases/detail.html'
    slug_field = 'pk'
    model = Case

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        category = context['object'].category.name
        context['category'] = category
        context['object'].start_date = context['object'].start_date if context['object'].start_date else datetime.now()
        context['object'].end_date = context['object'].end_date if context['object'].end_date else datetime.now()


        types = [ type_[1].lower() for type_ in context['object'].TYPE_CATEGORIES ]
        context['types'] = types
        
        categories = Category.objects.all()
        categoryNames = [cat.name for cat in categories]
        context['categoryNames'] = categoryNames

        relatedEvents = context['object'].events.all()


        events = [{
            'id': event.id,
            'identification': event.identification,
            'confirmed': event.confirmed,
            'start_date': datetime.strftime(utc_aware_date(event.start_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
            'end_date': datetime.strftime(utc_aware_date(event.end_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
            'public_evidence': event.public_evidence,
            'private_evidence': event.private_evidence,
            'issue_type': event.issue_type,
            'it_continues': event.it_continues,
            'domain': event.domain.domain_name,
            'asn': event.asn.asn,
            'closed': event.closed

        } for event in relatedEvents]
        context['events'] = events

        return context

    def post(self, request, *args, **kwargs):

        post = dict(request.POST)
        category = Category.objects.filter(name = post['category'][0]).first()

        case = Case.objects.get(id = post['id'][0])
        is_active = case.is_active
        manual_is_active = case.manual_is_active
        start_date_manual, end_date_manual = None, None 
        start_date, end_date = case.start_date, case.end_date


        print(post)

        if post['start_date'][0]:
            start_date_manual = datetime.strptime(post['start_date'][0], '%Y-%m-%d %H:%M')
            start_date = start_date_manual

        if post['end_date'][0]:
            end_date_manual = datetime.strptime(post['end_date'][0], '%Y-%m-%d %H:%M')
            end_date = end_date_manual
            if end_date_manual > datetime.now(): is_active = True 
            elif end_date_manual < datetime.now(): is_active = False

        try:

            Case.objects.filter(id = post['id'][0]).update(
                title = post['title'][0],
                title_eng = post['title_eng'][0],
                description = post['description'][0],
                description_eng = post['description_eng'][0],
                start_date = start_date,
                start_date_manual = start_date_manual,
                end_date = end_date,
                end_date_manual = end_date_manual,
                case_type = post['case_type'][0].lower(),
                category = category,
                twitter_search = post['twitter_search'][0],
                is_active = is_active,
                manual_is_active = manual_is_active

            )     

            return redirect('/dashboard/cases/detail/' + post['id'][0])

        except Exception as e:
            return HttpResponseBadRequest()

class EventsUnlinking(VSFLoginRequiredMixin, View):
    def get(self, request, **kwargs):

        get = self.request.GET or {}
        events = get.getlist('events[]')
        case_id = get.get('case')
        case_object = get_object_or_404(Case, pk=case_id)
        
        case_object.events.remove(*case_object.events.filter(id__in=events))
        case_object.save()

        return HttpResponse("OK")
        
class CaseDeleteView(VSFLoginRequiredMixin, View):
    def get(self, request, **kwargs):

        get = self.request.GET or {}
        cases = get.getlist('cases[]')

        for case_id in cases:
            case = get_object_or_404(Case, pk=case_id)
            to_be_orphaned_as = [event for event in case.events.all()]
            if len(to_be_orphaned_as)>0:
                for event in to_be_orphaned_as:
                    case.events.remove(event)
            case.delete()

        return HttpResponse("OK")

class EditEvents(VSFLoginRequiredMixin, DetailView):

    """
        Edit events related to one case.
        Expected GET Arguments:
            - id: Case id.
    """
    template_name = 'cases/edit-events.html'
    slug_field = 'pk'
    model = Case


    def get_context_data(self, **kwargs):
        get, prefill = self.request.GET or {}, {}
        context = super().get_context_data(**kwargs)
        relatedEvents = context['object'].events.all()

        fields = [ 
            'identification', 'confirmed', 'issue_type', 'domain', 'asn'
        ]

        for field in fields:
            getter = get.get(field)
            prefillAux = getter if getter else ""
            prefill[field] = prefillAux

        start_time = get.get("start_time")
        if start_time:
            prefill['start_time'] = start_time 
        
        end_time = get.get("end_time")
        if end_time:
            prefill['end_time'] = end_time

        context['prefill'] = prefill


        events = [{
            'id': event.id,
            'identification': event.identification,
            'confirmed': event.confirmed,
            'start_date': event.start_date,
            'end_date': event.end_date,
            'public_evidence': event.public_evidence,
            'private_evidence': event.private_evidence,
            'issue_type': event.issue_type,
            'it_continues': event.it_continues,
            'domain': event.domain.domain_name,
            'asn': event.asn.asn,
            'closed': event.closed

        } for event in relatedEvents]
        context['events'] = events
        
        return context

    def post(self, request, *args, **kwargs):
        post = dict(request.POST)
        caseID = post['case'][0]
        case = get_object_or_404(Case, pk=caseID)

        try:
            if 'eventsToDelete[]' in post:
                for eventID in post['eventsToDelete[]']:
                    event = Event.objects.get(id = eventID)
                    case.events.remove(event)
            
            if 'eventsSelected[]' in post:
                newEvents = Event.objects.filter(id__in=post['eventsSelected[]']).all()
                case.events.add(*newEvents)

            ordered_by_start_date = case.events.order_by('start_date')
            ordered_by_end_date = case.events.order_by('end_date')
            start_date_automatic = ordered_by_start_date.first().start_date.replace(tzinfo=None) or None
            end_date_automatic = ordered_by_end_date.last().end_date.replace(tzinfo=None) or None

            case.start_date_automatic = start_date_automatic
            case.end_date_automatic = end_date_automatic
            if not case.manual:
                case.start_date = start_date_automatic
                case.end_date = end_date_automatic
            
            return JsonResponse({'error' : None})
        except Exception as e:
            return HttpResponseBadRequest()

class CasePublish(VSFLoginRequiredMixin, View):

    def post(self, request, **kwargs):
        
        post = dict(request.POST)
        
        casesIds = post['cases[]']
        casesObjetcs = Case.objects.filter(id__in=casesIds).all()
        try:
            for case in casesObjetcs:
                if case.published:
                    case.published = False
                else:
                    case.published = True
                case.save()
            return JsonResponse({'error' : None})
        except Exception as e:
            return HttpResponseBadRequest()


class CaseChangeToAutomatic(VSFLoginRequiredMixin, View):

    def post(self, request, **kwargs):
        post = dict(request.POST)
        case_id = int(post['cases[]'][0])
        case = Case.objects.get(id = case_id)
        date_type = post['date'][0]
        
        try:
            if not (case.start_date_automatic and case.end_date_automatic):
                return JsonResponse({'error' : 'There are no events associated to this case'})

            if date_type == 'start_date':

                Case.objects.filter(id = case_id).update(
                    start_date = case.start_date_automatic,
                    start_date_manual = None,
                )
            elif date_type == 'end_date':

                is_active = False
                if case.end_date_automatic:
                    if case.end_date_automatic.replace(tzinfo=None) > datetime.now(): is_active = True 


                Case.objects.filter(id = case_id).update(
                    end_date = case.end_date_automatic,
                    end_date_manual = None,
                    is_active = is_active
                )

            else:
                is_active = False
                if case.end_date_automatic:
                    if case.end_date_automatic.replace(tzinfo=None) > datetime.now(): is_active = True 

                Case.objects.filter(id = case_id).update(
                    start_date = case.start_date_automatic,
                    start_date_manual = None,
                    end_date = case.end_date_automatic,
                    end_date_manual = None,
                    is_active = is_active
                )

            return JsonResponse({'error' : None})
        except Exception as e:
            print(e)
            return HttpResponseBadRequest()

class CaseChangeToActive(VSFLoginRequiredMixin, View):

    def post(self, request, **kwargs):
        post = dict(request.POST)
        case_id = int(post['cases[]'][0])
        case = Case.objects.get(id = case_id)
        try:

            Case.objects.filter(id = case_id).update(
                is_active = True,
                manual_is_active = True
            )
            return JsonResponse({'error' : None})
        except Exception as e:
            print(e)
            return HttpResponseBadRequest()