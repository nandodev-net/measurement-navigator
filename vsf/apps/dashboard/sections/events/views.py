# Django imports
from django.views.generic           import TemplateView

# Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin

# Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from datetime                                   import datetime, timedelta

# Local imports
from apps.main.events.models    import Event

class EventsList(VSFLoginRequiredMixin, TemplateView):

    template_name = "events-templates/list-events.html"

    def get_context_data(self, **kwargs):

        get, prefill = self.request.GET or {}, {}
        issueTypes = Event.IssueType.choices
        issueTypes = list(map(lambda m: {'name': m[1], 'value': m[0]}, issueTypes))

        # ------------------ making prefill ------------------ #
        
        fields = [ 
            'identification', 'confirmed', 'start_date', 'end_date', 
            'public_evidence', 'private_evidence', 'issue_type', 'domain', 'asn'
        ]

        for field in fields:
            prefillAux = get.get(field)
            if field == 'start_date' and not prefill:
                prefillAux = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            elif prefill:
                prefill['field'] = prefillAux

        # ---------------------------------------------------- #

        context = super().get_context_data()
        context['prefill'] = prefill
        context['issueTypes'] = issueTypes
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

        filters = {
            key: value
            for key, value in self.request.GET.items()
            if key in [ 
                'identification', 'confirmed', 'public_evidence', 
                'private_evidence', 'issue_type', 'domain', 'asn'
            ] and value != None and value != ""
        }
        qs.filter(**filters)

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
                'domain': event.domain, 
                'asn': event.asn
            })

        return response