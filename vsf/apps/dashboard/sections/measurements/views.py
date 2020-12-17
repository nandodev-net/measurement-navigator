#Django imports
from django.http.response import Http404
from django.views.generic           import TemplateView
from apps.main.measurements import submeasurements
#Inheritance imports
from vsf.views                      import VSFLoginRequiredMixin
#Third party imports
from django_datatables_view.base_datatable_view import BaseDatatableView
from typing                                     import List
from datetime                                   import datetime
#Utils import
from vsf.utils                                  import MeasurementXRawMeasurementXSite
from apps.main.measurements.utils               import search_measurement_by_queryset, search_measurement
#Local imports
from apps.main.sites.models                     import Site
from apps.main.asns                             import models as AsnModels
from apps.main.measurements                     import models as MeasModels
from apps.main.measurements.submeasurements     import models as SubMModels


# --- MEASUREMENTS VIEWS --- #

class ListMeasurementsTemplate(VSFLoginRequiredMixin, TemplateView):
    """
        This is the template that just renders the dynamic table listing
        measurements. All the interaction logic is in the DataBack view.

        This view can receive some special input to pre-fill some input search
        fields.
            Possible inputs:
                - input: Measurement input
                - since: Measurement start time lower bound
                - until: Measurement start time upper bound
                - site: site id for every measurement
                - anomaly: true, false, or an empty string
                - test_name: name of the test for all measurements
    """

    template_name = 'measurements-templates/list-measurements.html'

    def get_context_data(self, **kwargs):
        """
            Return in the context:
                test_types: The list of available test types
                sites: Site objects describing a site by id, name and description
                pre-fill: additional searching values to pre-fill the search parameters
        """
        # Note that the 'choices' member in a textchoice returns a
        # list of pairs [(s1, s2)] where s2 is the human readable (label) of the choice
        # and s1 is the value itself of the choice
        test_types = MeasModels.RawMeasurement.TestTypes.choices
        test_types = list(map(lambda m: {'name':m[1], 'value':m[0]}, test_types))

        # Now the available sites:
        sites = Site.objects.all().values('name', 'description_spa', 'description_eng', 'id')

        # Get the pre-fill search fields
        get = self.request.GET or {}
        prefill = {}

        inpt = get.get("input")
        if inpt:
            prefill['input'] = inpt

        since = get.get("since")
        if since:
            prefill['since'] = since

        until = get.get("until")
        if until:
            prefill['until'] = until

        site = get.get("site")
        if site:
            prefill['site'] = site

        anomaly = get.get("anomaly")
        if anomaly:
            prefill['anomaly'] = anomaly

        asn = get.get("asn")
        if asn:
            prefill['asn'] = asn

        test_name = get.get('test_name')
        if test_name:
            prefill['test_name'] = test_name

        # Get the most recent measurement:
        last_measurement_date = MeasModels\
                                .Measurement\
                                .objects.all()\
                                .order_by("-raw_measurement__measurement_start_time")\
                                .values("raw_measurement__measurement_start_time")\
                                .first()
                                
        #   If there is no measurements, result is going to be none, cover that case.
        if last_measurement_date is None:
            last_measurement_date = "No measurements yet"
        else:
            last_measurement_date = datetime.strftime(last_measurement_date["raw_measurement__measurement_start_time"], "%Y-%m-%d %H:%M:%S")

        context = super().get_context_data()
        context['test_types'] = test_types
        context['sites'] = sites
        context['prefill'] = prefill
        context['asns'] = AsnModels.ASN.objects.all()
        context['last_measurement_date'] = last_measurement_date
        return context

class ListMeasurementsBackEnd(BaseDatatableView):
    """
        This is the backend view for the ListMeasurementsDataTable view, who
        just renders the template

        List All Measurements based on the following columns:
            * Input
            * TestName
            * ASN
            * Country Code
            * Site

        This View requires datatables to send server-side
        paginated data to the front, and it's highly coupled
        with its corresponding template.
    """
    columns = [
            'raw_measurement__input',
            'raw_measurement__test_name',
            'raw_measurement__measurement_start_time',
            'raw_measurement__probe_asn',
            'raw_measurement__probe_cc',
            'site_name',
            'anomaly'
        ]

    order_columns = [
            'raw_measurement__input',
            'raw_measurement__test_name',
            'raw_measurement__measurement_start_time',
            'raw_measurement__probe_asn',
            'raw_measurement__probe_cc',
            'site_name',
            'anomaly'
        ]

    def get_initial_queryset(self):
        return MeasurementXRawMeasurementXSite()

    def filter_queryset(self, qs):
        # Get request params
        get = self.request.GET or {}

        ## Ok this is the kind of solution that i don't like

        # Parse the input data
        input       = get.get('input')
        test_name   = get.get('test_name')
        since       = get.get('since')
        ASN         = get.get('asn')
        country     = get.get('country')
        anomaly     = get.get('anomaly')
        until       = get.get('until')
        site        = get.get('site')

        # Get desired measurements
        measurements = search_measurement_by_queryset(
            qs,
            since=since,
            test_name=test_name,
            ASN=ASN,
            input=input,
            country=country,
            until=until,
            site=site,
            anomaly= anomaly.lower() == "true" if anomaly != None else None
        )

        return measurements

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []
        for item in qs:
            json_data.append({
                'raw_measurement__measurement_start_time':item.raw_measurement.measurement_start_time,
                'raw_measurement__probe_cc':item.raw_measurement.probe_cc,
                'raw_measurement__probe_asn':item.raw_measurement.probe_asn,
                'raw_measurement__input':item.raw_measurement.input,
                'raw_measurement__test_name':item.raw_measurement.test_name,
                'id' : item.id,
                'site' : item.site,
                'site_name' : item.site_name or "(no site)",
                'anomaly' : item.anomaly
            })
        return json_data

class MeasurementDetails(VSFLoginRequiredMixin, TemplateView):
    """
        Given the uuid "id" for some measurement, return a page with the following
        data passed within context:
            + measurement: The simple measurement object itself
            + submeasurements: A dict object with the following fields:
                - dns  : A list (possibly empty) with dns submeasurements
                - tcp  : A list (possibly empty) with tcp submeasurements
                - http : A list (possibly empty) with http submeasurements
            + error : a string specifying an error type
                - id_not_specified : unable to find an 'id' atribute in the get request
                - not_found        : there's no measurement with the provided id
                - null             : Everything ok
        Possible error:


    """
    template_name = "measurements-templates/detailed-info-url.html"

    def get_context_data(self, **kwargs):


        # Get the context so far
        context = super().get_context_data()

        # Get the measurement
        # id = kwargs.get('id')
        id = self.request.GET.get('id')
        # Raise 404 if id is not provided
        if id is None:
            context['error'] = 'id_not_provided'
            return context
        
        # Raise 404 if id cannot be found or if such id is an invalid one
        try:
            measurement = MeasModels.Measurement.objects.get(id=id)
        except:
            context['error'] = 'not_found'
            return context

        # List the models, so it is easy to change when adding new submeasurement models
        models : List[(SubMModels.SubMeasurement, str)] = [ (SubMModels.DNS, 'dns'), 
                                                            (SubMModels.TCP, 'tcp'), 
                                                            (SubMModels.HTTP, 'http')
                                                        ]

        # Ask every submeasurement related to this measurement for each type
        context['submeasurements'] = {}
        for (Model, label) in models:
            context['submeasurements'][label] = Model.objects.filter(measurement=measurement)

        # Return the context
        context['measurement'] = measurement
        context['error'] = None
        return context