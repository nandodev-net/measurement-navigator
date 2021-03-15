# Django imports
from django.views.generic           import TemplateView, ListView, UpdateView, View, DetailView
from django.shortcuts               import get_object_or_404, redirect, render
from django.http.response           import HttpResponseBadRequest
from django.http                    import JsonResponse
from django.core.serializers.json   import DjangoJSONEncoder

# Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin

# Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from datetime                                   import datetime, timedelta
import json

# Local imports
from apps.main.events.models    import Event
from apps.main.cases.models     import Case
from apps.main.asns.models      import ASN

from .forms                     import EventForm


class EventsList(VSFLoginRequiredMixin, ListView):
    queryset = Event.objects.all()
    template_name = "events/list-events.html"

    def get_context_data(self, **kwargs):

        get, prefill = self.request.GET or {}, {}
        issueTypes = Event.IssueType.choices
        issueTypes = list(map(lambda m: {'name': m[1].upper(), 'value': m[0]}, issueTypes))

        # ------------------ making prefill ------------------ #
        
        fields = [ 
            'identification', 'confirmed', 'start_date', 'end_date', 
            'public_evidence', 'private_evidence', 'issue_type', 'domain', 'asn'
        ]

        for field in fields:
            getter = get.get(field)
            prefillAux = getter if getter else ""
            if field == 'start_date' and not prefill:
                prefillAux = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            elif field:
                prefill[field] = prefillAux

        # ---------------------------------------------------- #

        context = super().get_context_data()
        context['prefill'] = prefill
        context['issueTypes'] = issueTypes
        context['asns'] = ASN.objects.all()

        return context

    def post(self, request, *args, **kwargs):
        post = dict(request.POST)
        
        eventsIds = post['events[]']
        cases = post['cases[]']

        eventsObjetcs = Event.objects.filter(id__in=eventsIds).all()
        casesObjects = Case.objects.filter(title__in=cases).all()

        try:
            for case in casesObjects:
                case.events.set(eventsObjetcs)
            return JsonResponse({'error' : None})

        except Exception as e:
            print(e)
            return HttpResponseBadRequest()

class EventsData(BaseDatatableView):

    columns = [ 
        'identification', 'confirmed', 'start_date', 'end_date', 
        'public_evidence', 'private_evidence', 'issue_type', 'domain', 'asn'
    ]

    order_columns = columns

    def get_initial_queryset(self):
        return Event.objects.all()

    def filter_queryset(self, qs):

        #--------- Filtering datetime fields ---------#

        start_date = self.request.GET.get('start_date')
        if start_date != None and start_date != "":
            qs = qs.filter(start_date__gte = start_date)

        end_date = self.request.GET.get('end_date')
        if end_date != None and end_date != "":
            qs = qs.filter(end_date__lte = end_date)

        #---------------------------------------------#

        #------- Another type of data filtering ------#

        # Check later
        """filters = {
            key: value
            for key, value in self.request.GET.items()
            if key in [ 
                'identification', 'confirmed', 'public_evidence', 
                'private_evidence', 'issue_type', 'domain', 'asn'
            ] and value != None and value != ""
        }
        qs.filter(**filters)"""

        identification = self.request.GET.get('identification')
        if identification != None and identification != "":
            qs = qs.filter(identification = identification)


        confirmed = self.request.GET.get('confirmed')
        
        if confirmed != None and confirmed != "":
            if confirmed == 'true': 
                qs = qs.filter(confirmed = 't') 
            else: 
                qs = qs.filter(confirmed = 'f')


        public_evidence = self.request.GET.get('public_evidence')
        if public_evidence != None and public_evidence != "":
            qs = qs.filter(public_evidence = public_evidence)

        private_evidence = self.request.GET.get('private_evidence')
        if private_evidence != None and private_evidence != "":
            qs = qs.filter(private_evidence = private_evidence)

        issue_type = self.request.GET.get('issue_type')
        if issue_type != None and issue_type != "":
            qs = qs.filter(issue_type = issue_type)


        asn = self.request.GET.get('asn')

        if asn != None and asn != "":
            qs = qs.filter(asn__asn = asn)

        #---------------------------------------------#

        return qs

    def prepare_results(self, qs):

        response = []
        for event in qs:

            try:
                case = event.cases.latest('id').title
            except:
                case = None

            response.append({
                'id': event.id,
                'identification': event.identification,
                'issue_type': event.issue_type, 
                'confirmed': event.confirmed, 
                'start_date': event.start_date, 
                'end_date': event.end_date, 
                'domain': event.domain.domain_name, 
                'asn': event.asn.asn,
                'case': case,
                "actions": {"confirmed": event.confirmed}
            })

        return response

class EventUpdateView(VSFLoginRequiredMixin, UpdateView):
    form_class = EventForm
    model = Event 
    queryset = Event.objects.all()
    template_name = "events/event-edit-form.html"
    success_url = "/dashboard/events/"

    def get_context_data(self, **kwargs):

        context = super(EventUpdateView, self).get_context_data(**kwargs)
        query = get_object_or_404(Event, pk=self.kwargs['pk'])

        context['event_start_date'] = query.start_date

        if query.issue_type == Event.IssueType.DNS:
            submeasurements = query.dns_list.all()
        elif query.issue_type == Event.IssueType.HTTP:
            submeasurements = query.http_list.all()
        elif query.issue_type == Event.IssueType.TCP:
            submeasurements = query.tcp_list.all()
        else:
            raise ValueError(f"Unexpected query type: {query.issue_type}")

        context['measurements'] = []

        for i in submeasurements:
            context['measurements'].append(
                {
                    'measurement_id':i.measurement.id,
                    'raw_meas_id':i.measurement.raw_measurement.id,
                    'raw_start_time':i.measurement.raw_measurement.measurement_start_time,
                })

        return context  


    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):

        self.object.confirmed = form.cleaned_data['confirmed']
        self.object.public_evidence = form.cleaned_data['public_evidence']
        self.object.private_evidence = form.cleaned_data['private_evidence']        
        self.object.save()

        return HttpResponseRedirect("/dashboard/events/")


    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                form=form
            )
        )

class EventDetailData(VSFLoginRequiredMixin, View):

    """
        Returns information about a specific event.
        Expected GET Arguments:
            - id: Case id.
    """

    def get(self, request, **kwargs):

        get = self.request.GET or {}
        eventId = get.get('id')

        if eventId != None:
            eventObj = Event.objects.get(id = eventId)
            
            data = {
                "identification": eventObj.identification,
                "start_date": eventObj.start_date,
                "end_date": eventObj.end_date,
                "public_evidence": eventObj.public_evidence,
                "private_evidence": eventObj.private_evidence,
                "issue_type": eventObj.issue_type,
                "domain": eventObj.domain.domain_name,
                "asn": eventObj.asn.asn,
            }
            
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({})


class EventDetailView(DetailView):
    template_name = 'events/detail.html'
    slug_field = 'pk'
    model = Event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(context['object'].__dict__)
        return context