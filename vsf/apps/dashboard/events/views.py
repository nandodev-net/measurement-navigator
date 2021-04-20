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
from apps.main.measurements.models import Measurement
from apps.main.events.models    import Event
from apps.main.cases.models     import Case
from apps.main.asns.models      import ASN
from apps.main.measurements.submeasurements.models import DNS, HTTP, TCP
from apps.main.sites.models import Domain
from apps.main.asns.models import ASN
from .forms                     import EventForm
from ..utils import *


class EventsList(VSFLoginRequiredMixin, ListView):
    queryset = Event.objects.all()
    template_name = "events/list-events.html"

    def get_context_data(self, **kwargs):

        get, prefill = self.request.GET or {}, {}
        issueTypes = Event.IssueType.choices
        issueTypes = list(map(lambda m: {'name': m[1].upper(), 'value': m[0]}, issueTypes))

        # ------------------ making prefill ------------------ #
        
        fields = [ 
            'identification', 'confirmed', 'issue_type', 'domain', 'asn'
        ]

        for field in fields:
            getter = get.get(field)
            prefillAux = getter if getter else ""
            prefill[field] = prefillAux

        start_time = get.get("start_time") or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        prefill['start_time'] = start_time 
        
        end_time = get.get("end_time")
        if end_time:
            prefill['end_time'] = end_time

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

class EventsData(VSFLoginRequiredMixin, BaseDatatableView):

    columns = [ 
        'identification', 'confirmed', 'start_date', 'end_date', 
        'issue_type', 'domain', 'asn'
    ]

    order_columns = columns

    def get_initial_queryset(self):
        return Event.objects.all()

    def filter_queryset(self, qs):

        #--------- Filtering datetime fields ---------#

        start_time = self.request.GET.get('start_time')
        if start_time != None and start_time != "":
            start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d')
            utc_start_time = utc_aware_date(start_time)
            qs = qs.filter(start_date__gte = utc_start_time)

        end_time = self.request.GET.get('end_time')
        if end_time != None and end_time != "":
            end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d')
            utc_end_time = utc_aware_date(end_time)
            qs = qs.filter(end_date__lte = utc_end_time)

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

        issue_type = self.request.GET.get('issue_type')
        if issue_type != None and issue_type != "":
            qs = qs.filter(issue_type = issue_type)


        asn = self.request.GET.get('asn')
        if asn != None and asn != "":
            qs = qs.filter(asn__asn = asn)

        domain = self.request.GET.get('domain')
        if domain != None and domain != "":
            qs = qs.filter(domain__domain_name__contains = domain)

        #---------------------------------------------#

        return qs

    def prepare_results(self, qs):

        response = []
        for event in qs:

            try:
                case = event.cases.latest('id').title
            except:
                case = None
                
            # Compute start date
            start_date = event.get_start_date()
            if start_date:
                start_date = start_date.astimezone(CARACAS).strftime("%b. %d, %Y, %H:%M %p")

            # Compute end date
            end_date = event.get_end_date()
            if end_date:
                end_date = end_date.astimezone(CARACAS).strftime("%b. %d, %Y, %H:%M %p")

            response.append({
                'id': event.id,
                'identification': event.identification,
                'issue_type': event.issue_type, 
                'confirmed': event.confirmed, 
                'start_date': start_date, 
                'end_date': end_date, 
                'domain': event.domain.domain_name, 
                'asn': event.asn.asn,
                'case': case if case else "-No case related-",
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
                "start_date": eventObj.start_date.astimezone(CARACAS).strftime("%b. %d, %Y, %H:%M %p"),
                "end_date": eventObj.end_date.astimezone(CARACAS).strftime("%b. %d, %Y, %H:%M %p"),
                "public_evidence": eventObj.public_evidence,
                "private_evidence": eventObj.private_evidence,
                "issue_type": eventObj.issue_type,
                "domain": eventObj.domain.domain_name,
                "asn": eventObj.asn.asn,
            }
            
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({})
            
class EventDetailView(VSFLoginRequiredMixin, DetailView):
    template_name = 'events/detail.html'
    slug_field = 'pk'
    model = Event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(context['object'].__dict__)
        issue_type = context['object'].issue_type
        queryStr = issue_type + '.objects.all()'
        submeasures = eval(queryStr)
        submeasuresRelated = submeasures.filter(event = context['object'].id)
        
        context['submeasures'] = [
            {
                'start_time': sub.measurement.raw_measurement.measurement_start_time.astimezone(CARACAS).strftime("%b. %d, %Y, %H:%M %p"),
                'probe_cc': sub.measurement.raw_measurement.probe_cc,
                'probe_asn': sub.measurement.raw_measurement.probe_asn,
                'input': sub.measurement.raw_measurement.input,
                'id': sub.measurement_id,
                'site': sub.measurement.domain.site.id if sub.measurement.domain and sub.measurement.domain.site else -1,
                'site_name': sub.measurement.domain.site.name if sub.measurement.domain and sub.measurement.domain.site else "(no site)",
                'measurement_anomaly': sub.measurement.anomaly,
                'flag_type': sub.flag_type,

            } for sub in submeasuresRelated
        ]

        issueTypes = Event.IssueType.choices
        issueTypes = list(map(lambda m: {'name': m[1].upper(), 'value': m[0]}, issueTypes))
        context['issueTypes'] = issueTypes
        
        caseRelated = Case.objects.filter(events = context['object']).first()
        context['case'] = caseRelated.__dict__ if caseRelated else {}
        context['case']['category'] = caseRelated.category.name if caseRelated else ""
        context['asns'] = ASN.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        post = dict(request.POST)

        identification = post['identification'][0]
        start_date = post['start_time'][0]
        end_date = post['end_date'][0]
        public_evidence = post['public_evidence'][0]
        private_evidence = post['private_evidence'][0]
        domain = post['domain'][0]
        asn = post['asn'][0]



        try:
            domainId = Domain.objects.filter(domain_name = domain).first().id 
            asnId = ASN.objects.filter(asn = asn).first().id 

            Event.objects.filter(identification = identification).update(
                identification = identification,
                start_date = start_date,
                end_date = end_date,
                public_evidence = public_evidence,
                private_evidence = private_evidence,
                domain = domainId,
                asn = asnId
            )

            return redirect('/dashboard/events/detail/' + post['id'][0])

        except Exception as e:
            print(e)
            return HttpResponseBadRequest()

class EventConfirm(VSFLoginRequiredMixin, View):

    def post(self, request, **kwargs):
        
        post = dict(request.POST)
        
        eventsIds = post['events[]']
        eventsObjetcs = Event.objects.filter(id__in=eventsIds).all()
        try:
            for event in eventsObjetcs:
                if event.confirmed:
                    event.confirmed = False
                else:
                    event.confirmed = True
                event.save()
            return JsonResponse({'error' : None})
        except Exception as e:
            print(e)

class EventsByMeasurement(VSFLoginRequiredMixin, View):
    def get(self, request, **kwargs):
        post = dict(request.GET)

        measurementId = post['id']
        event_list = []
        event_json = []

        try:
            dns_objs = DNS.objects.filter(measurement__id = measurementId)
            for instance in dns_objs:
                if instance.event:
                    event_list.append(instance.event)
        except:
            pass
        try:
            tcp_objs = TCP.objects.get(measurement__id = measurementId)
            for instance in tcp_objs:
                if instance.event:
                    event_list.append(instance.event)
        except:
            pass
        try:
            http_objs = HTTP.objects.get(measurement__id = measurementId)
            for instance in http_objs:
                if instance.event:
                    event_list.append(instance.event)           
        except:
            pass

        if event_list:
            for event in event_list:
                event_row = {
                    'id':event.id,
                    'identification':event.identification,
                    'event_type':event.issue_type,
                    'confirmed':event.confirmed,
                    'start_date':event.start_date.astimezone(CARACAS).strftime("%b. %d, %Y, %H:%M %p"),
                    'end_date':event.end_date,
                    'domain':event.domain,
                    'asn':event.asn,
                }
                event_json.append(event_row)
                
            return JsonResponse(event_json)
        else:
            return JsonResponse({'error' : None})







