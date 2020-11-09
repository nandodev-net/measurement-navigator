# WARNING: There's a lot of fields that require to be checked at some point,
# they're marked as @TODO, please fix this configuration before launching
# the production build


 # Django imports: 
from django.db import models
from django.contrib.postgres.fields import JSONField

# third party imports:
import uuid

# Local imports
# from .submeasurements.models  import SubMeasurement
# from .submeasurements.utils  import createSubMeasurements


class RawMeasurement(models.Model):
    """
        This models holds the information provided by an ooni
        measurement. We may not work with this model directly, instead, 
        we should work with the Measurement model, which is an abstraction 
        layer for this model.
    """

    class TestTypes(models.TextChoices):
        """
            An enum with the valid test names
        """
        WEB_CONNECTIVITY = 'web_connectivity', ('Web Connectivity') #
        HTTP_REQUESTS = 'http_requests', ('HTTP Requests') #
        DNS_CONSISTENCY = 'dns_consistency', ('DNS Consistency') #
        HTTP_INVALID_REQUEST_LINE = 'http_invalid_request_line', ('HTTP Invalid Request Line') #
        BRIDGE_REACHABILITY = 'bridge_reachability', ('Bridge Reachability') # need help
        TCP_CONNECT = 'tcp_connect', ('TCP Connect') #
        HTTP_HEADER_FIELD_MANIPULATION = 'http_header_field_manipulation', ('HTTP header field manipulation') #
        HTTP_HOST = 'http_host', ('HTTP host') #
        MULTI_PROTOCOL_TRACEROUTE = 'multi_protocol_traceroute', ('Multi-protocol Traceroute') # need help
        MEEK_FRONTED_REQUESTS_TEST = 'meek_fronted_requests_test', ('Meek Frontend request test') #
        WHATSAPP = 'whatsapp', ('Whatsapp') #
        VANILLA_TOR = 'vanilla_tor', ('Vanilla tor') #
        FACEBOOK_MESSENGER = 'facebook_messenger', ('Facebook Messenger') #
        NDT = 'ndt', ('NDT')
        DASH = 'dash', ('DASH') 
        TELEGRAM = 'telegram', ('Telegram') #
        PSIPHON = 'psiphon', ('Psiphon') #
        TOR = 'tor', ('Tor') #
        sni_blocking = 'sni_blocking', ('SNI Blocking') #
        UNKNOWN = 'unknown', ('UNKNOWN')

    _DATABASE = 'titan_db'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    input = models.TextField(null=True)
    annotations = JSONField()
    report_id = models.CharField(max_length=100)
    report_filename = models.CharField(max_length=250)
    options = models.TextField(null=True)
    probe_cc = models.CharField(max_length=50)
    probe_asn = models.CharField(max_length=50)
    probe_ip = models.GenericIPAddressField()
    data_format_version = models.CharField(max_length=100)
    test_name = models.CharField(max_length=60, choices=TestTypes.choices)
    test_start_time = models.DateTimeField()
    measurement_start_time = models.DateTimeField()
    test_runtime = models.FloatField()
    test_helpers = models.TextField(null=True)
    software_name = models.CharField(max_length=30)
    software_version = models.CharField(max_length=100)
    test_version = models.CharField(max_length=100)
    bucket_date = models.DateTimeField()

    # ---------------------------------------------- #
    test_keys = JSONField()
    # This is the important part for the flags logic,
    # for every test type, there's specific data related to the
    # result for that test, and that data is stored in this json field
    # ---------------------------------------------- #


    def save(   self, 
                force_insert=False, 
                force_update=False, 
                using=None,
                update_fields=None):
        # When creating a new RawMeasurement, we have to add an entry
        # for the Measurement table pointing to this new model
        super().save(force_insert, force_update, using, update_fields)


        # To avoid circular imports, we need to import this here:
        from .submeasurements.utils  import createSubMeasurements
        from .utils import anomaly
        
        measurement = Measurement(raw_measurement=self, anomaly=anomaly(self))
        try:
            measurement.save()
        except:
            # try to delete the already stored raw measurement
            # if there was an error in somthing else
            for m in RawMeasurement.objects.all(id=self.id):
                m.delete()
            return
        subMeasurements = createSubMeasurements(self)

        for sb in subMeasurements:
            sb.measurement = measurement
            try:
                sb.save()
            except: 
                pass # I think we should put some loggin here @TODO

        

class Measurement(models.Model):
    """
        This model is an abstraction layer for 
        the RawMeasurement model, which contains the information 
        provided by ooni for each measurement. Our application
        logic will reside instead in this model.
    """
    # Measurement raw data
    raw_measurement = models.OneToOneField(
                            to=RawMeasurement, 
                            on_delete=models.CASCADE,
                            null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)

    anomaly = models.BooleanField(default=False)

