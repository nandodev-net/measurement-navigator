# Django imports
from django.views.generic           import ListView, UpdateView, View, DetailView
from django.shortcuts               import get_object_or_404, redirect
from django.http.response           import HttpResponseBadRequest
from django.http                    import JsonResponse
from django.db.models               import Q

# Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin

# Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from datetime                                   import datetime, timedelta
import json

# Local imports
from apps.main.measurements.models  import RawMeasurement
from apps.main.sites.models         import Site
from apps.main.events.models        import Event
from apps.main.cases.models         import Case
from apps.main.asns.models          import ASN
from apps.main.measurements.submeasurements.models import DNS, HTTP, TCP, SubMeasurement
from apps.main.sites.models         import Domain
from apps.main.asns.models          import ASN
from .forms                         import EventForm
from ..utils import *


class EventsList(VSFLoginRequiredMixin, ListView):
    queryset = Event.objects.all()
    template_name = "events/list-events.html"

    def get_context_data(self, **kwargs):

        get, prefill = self.request.GET or {}, {}
        issueTypes = Event.IssueType.choices
        issueTypes = list(map(lambda m: {'name': m[1].upper(), 'value': m[0]}, issueTypes))
        
        fields = [ 
            'identification', 'confirmed', 'issue_type', 'domain', 'site', 'asn', 'muted', 'it_continues'
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


        context = super().get_context_data()
        context['prefill'] = prefill
        context['issueTypes'] = issueTypes
        context['asns'] = ASN.objects.all()

        return context

    def post(self, request, *args, **kwargs):
        """
            This post requests refers to the -add event to case- feature
            which is implemented in the events list page
        """ 
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
            return HttpResponseBadRequest()

class EventsData(VSFLoginRequiredMixin, BaseDatatableView):

    columns = [ 
        'id', 'identification', 'issue_type', 'confirmed', 'start_date', 'end_date', 
        'domain__domain_name', 'asn__asn', 'muted'
    ]

    order_columns = [ 
        'id', '', 'issue_type', 'confirmed', 'start_date', 'end_date', 
        'domain__domain_name', 'asn__asn', 'muted'
    ]

    def get_initial_queryset(self):
        return Event.objects.all()


    def filter_queryset(self, qs):

        #--------- Filtering datetime fields ---------#
        start_time, end_time = self.request.GET.get('start_time'), self.request.GET.get('end_time')


        if start_time != None and start_time != "":
            start_time = datetime.strptime(start_time, '%Y-%m-%d')
            utc_start_time = utc_aware_date(start_time, self.request.session['system_tz'])
            qs = qs.filter(start_date__gte = utc_start_time) | qs.filter(manual_start_date__gte = utc_start_time)



        if end_time != None and end_time != "":
            end_time = datetime.strptime(end_time, '%Y-%m-%d')
            utc_end_time = utc_aware_date(end_time, self.request.session['system_tz'])
            qs = qs.filter(end_date__lte = utc_end_time) | qs.filter(manual_end_date__lte = utc_end_time)


        #--------- Filtering identification field ---------#
        identification = self.request.GET.get('identification')
        if identification != None and identification != "":
            qs = qs.filter(identification = identification)

        
        #--------- Filtering confirmation field ---------#
        confirmed = self.request.GET.get('confirmed')
        if confirmed != None and confirmed != "":
            if confirmed == 'true': 
                qs = qs.filter(confirmed = 't') 
            else: 
                qs = qs.filter(confirmed = 'f')


        #--------- Filtering muted field ---------#
        muted = self.request.GET.get('muted')
        if muted != None:
            if muted == 'true': 
                qs = qs.filter(muted = 't') 
            elif muted == 'false' or muted == '': 
                qs = qs.filter(muted = 'f')


        #--------- Filtering Issue field ---------#
        issue_type = self.request.GET.get('issue_type')
        if issue_type != None and issue_type != "":
            qs = qs.filter(issue_type = issue_type.lower())


        #--------- Filtering muted field ---------#
        asn = self.request.GET.get('asn')
        if asn != None and asn != "":
            qs = qs.filter(asn__asn = asn)

            
        #--------- Filtering domain field ---------#
        domain = self.request.GET.get('domain')
        if domain != None and domain != "":
            qs = qs.filter(domain__domain_name__contains = domain)

        #--------- Filtering site field ---------#
        site = self.request.GET.get('site')
        if site != None and site != "":
            qs = qs.filter(domain__site__name__contains = site)


        #--------- Filtering case field ---------#
        case = self.request.GET.get('case')
        if case != None:
            case_events = [event.id for event in Case.objects.filter(id = case).first().events.all()]
            qs = qs.exclude(id__in = case_events)

        #--------- Filtering Continuity ---------#
        it_continues = self.request.GET.get('it_continues')
        if it_continues:
            if it_continues == 'true': 
                qs = qs.filter(it_continues = 't') 
            elif it_continues == 'false' or it_continues == '': 
                qs = qs.filter(it_continues = 'f')
            
        return qs


    def prepare_results(self, qs):

        response = []
        for event in qs:
                
            # Compute start date
            start_date = event.start_date
            if start_date:
                start_date = start_date.strftime("%b. %d, %Y, %H:%M %p")

            # Compute end date
            end_date = event.end_date
            if end_date:
                end_date = end_date.strftime("%b. %d, %Y, %H:%M %p")
            
            if event.current_start_date:
                start_date = datetime.strftime(utc_aware_date(event.current_start_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S")
            else:
                start_date = datetime.strftime(utc_aware_date(event.start_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S")

            if event.current_end_date:
                end_date = datetime.strftime(utc_aware_date(event.current_end_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S")
            else:
                end_date = datetime.strftime(utc_aware_date(event.end_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S")

            response.append({
                'id': event.id,
                'identificator': event.id,
                'issue_type': event.issue_type, 
                'confirmed': event.confirmed, 
                'start_date': start_date,
                'is_manual_start_date':event.start_date_manual,
                'end_date': end_date,
                'is_manual_end_date':event.end_date_manual,
                'domain': event.domain.domain_name, 
                'site': event.domain.site.name if event.domain.site else "No site associated", 
                'asn': event.asn.asn,
                'muted': event.muted,
                'it_continues': event.it_continues
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
                'confirmed': eventObj.confirmed,
                'muted': eventObj.muted,
                "start_date": datetime.strftime(utc_aware_date(eventObj.start_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
                "end_date": datetime.strftime(utc_aware_date(eventObj.end_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
                "public_evidence": eventObj.public_evidence,
                "private_evidence": eventObj.private_evidence,
                "issue_type": eventObj.issue_type,
                "domain": eventObj.domain.domain_name,
                "asn": eventObj.asn.asn,
                "start_manual": eventObj.isStartDateManual(),
                "end_manual": eventObj.isEndDateManual(),
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
        issue_type = context['object'].issue_type

        status = "active"
        if context['object'].muted:
            status = "muted"
        if context['object'].closed:
            status = "closed"
        context['status'] = status 
        
        context['start_manual'] = context['object'].isStartDateManual()
        context['end_manual'] = context['object'].isEndDateManual()
        print(context['start_manual'])
        


        test_types = RawMeasurement.TestTypes.choices
        test_types = list(map(lambda m: {'name':m[1], 'value':m[0]}, test_types))
        sites = Site.objects.all().values('name', 'description_spa', 'description_eng', 'id')
        context['submeasurements_filter'] = {
            'test_types': test_types,
            'sites': sites,
            'flags': [ 'DNS', 'HTTP', 'TCP' ]
        }

        
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
        start_date = post['start_date'][0]
        end_date = post['end_date'][0]
        public_evidence = post['public_evidence'][0]
        private_evidence = post['private_evidence'][0]
        domain = post['domain'][0]
        asn = post['asn'][0]

        event = Event.objects.get(id = post['id'][0])

        try:
            domainId = Domain.objects.filter(domain_name = domain).first().id 
            asnId = ASN.objects.filter(asn = asn).first().id 

            if (( event.start_date != start_date and event.manual_start_date == None ) or 
                (event.manual_start_date != start_date and event.manual_start_date )):
                Event.objects.filter(id = post['id'][0]).update(
                    manual_start_date = start_date
                )

            if (( event.end_date != end_date and event.manual_end_date == None ) or 
                (event.manual_end_date != end_date and event.manual_end_date )):
                Event.objects.filter(id = post['id'][0]).update(
                    manual_end_date = end_date
                )

            Event.objects.filter(id = post['id'][0]).update(
                identification = identification,
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

class EventMute(VSFLoginRequiredMixin, View):

    def post(self, request, **kwargs):
        
        post = dict(request.POST)
        
        eventsIds = post['events[]']
        eventsObjetcs = Event.objects.filter(id__in=eventsIds).all()
        try:
            for event in eventsObjetcs:
                if event.muted:
                    event.muted = False
                else:
                    event.muted = True
                event.save()
            return JsonResponse({'error' : None})
        except Exception as e:
            print(e)

        """
        try:
            for event in eventsObjetcs:
                dns = DNS.objects.filter(event=event)
                http = HTTP.objects.filter(event=event)
                tcp = TCP.objects.filter(event=event)
                if event.muted: 
                    if len(dns) > 0:
                        for dns_sm in dns:
                            dns_sm.flag_type = SubMeasurement.FlagType.HARD
                            dns_sm.save() 

                    if len(http) > 0:
                        for http_sm in http:
                            http_sm.flag_type = SubMeasurement.FlagType.HARD   
                            http_sm.save() 


                    if len(tcp) > 0:
                        for tcp_sm in tcp:
                            tcp_sm.flag_type = SubMeasurement.FlagType.HARD
                            tcp_sm.save()               

                    event.muted = False
                    event.save()
                else:
                    if len(dns) > 0:
                        for dns_sm in dns:
                            dns_sm.flag_type = SubMeasurement.FlagType.MUTED
                            dns_sm.save()

                    if len(http) > 0:
                        for http_sm in http:
                            http_sm.flag_type = SubMeasurement.FlagType.MUTED  
                            http_sm.save() 

                    if len(tcp) > 0:
                        for tcp_sm in tcp:
                            tcp_sm.flag_type = SubMeasurement.FlagType.MUTED    
                            tcp_sm.save()               

                    event.muted = True
                    event.save()

            return JsonResponse({'error' : None})
        except Exception as e:
            print(e)
        """


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
                    'start_date':datetime.strftime(utc_aware_date(event.start_date, self.request.session['system_tz']), "%Y-%m-%d %H:%M:%S"),
                    'end_date':event.end_date,
                    'domain':event.domain,
                    'asn':event.asn,
                }
                event_json.append(event_row)
                
            return JsonResponse(event_json)
        else:
            return JsonResponse({'error' : None})







