# Django imports
from django.views.generic           import TemplateView

# Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin

# Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from datetime                                   import datetime, timedelta

# Local imports
from apps.main.events.models    import Event
from apps.main.asns.models      import ASN


class EventsList(VSFLoginRequiredMixin, TemplateView):

    template_name = "events-templates/list-events.html"

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
            prefillAux = get.get(field)
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
            qs = qs.filter(asn__name = asn)

        #---------------------------------------------#

        return qs

    def prepare_results(self, qs):

        response = []
        for event in qs:
            
            response.append({
                'identification': event.identification, 
                'confirmed': event.confirmed, 
                'start_date': event.start_date, 
                'end_date': event.end_date, 
                'public_evidence': event.public_evidence, 
                'private_evidence': event.private_evidence, 
                'issue_type': event.issue_type, 
                'domain': event.domain.domain_name, 
                'asn': event.asn.asn
            })

        return response