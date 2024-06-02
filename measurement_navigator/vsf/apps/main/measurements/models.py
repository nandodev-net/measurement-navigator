# WARNING: There's a lot of fields that require to be checked at some point,
# they're marked as @TODO, please fix this configuration before launching
# the production build


import sys
import uuid

# Django imports:
from django.db import models
from django.db.models import JSONField
from django.db.models.deletion import SET_NULL
# third party imports:
from django_prometheus.models import ExportModelOperationsMixin
from model_utils.models import TimeStampedModel

from apps.main.asns.models import ASN
# local imports
from apps.main.sites.models import Domain


# class RawMeasurement(TimeStampedModel):
class RawMeasurement(ExportModelOperationsMixin("RawMeasurement"), TimeStampedModel):
    """
    This models holds the information provided by an ooni
    measurement. We may not work with this model directly, instead,
    we should work with the Measurement model, which is an abstraction
    layer for this model.
    """

    index_together = [
        ["input", "report_id", "probe_asn", "test_name", "measurement_start_time"]
    ]  # This is used to quickly check if a given raw measurement is already in database

    class TestTypes(models.TextChoices):
        """
        An enum with the valid test names
        """

        WEB_CONNECTIVITY = "web_connectivity", ("Web Connectivity")  #
        HTTP_REQUESTS = "http_requests", ("HTTP Requests")  #
        DNS_CONSISTENCY = "dns_consistency", ("DNS Consistency")  #
        HTTP_INVALID_REQUEST_LINE = "http_invalid_request_line", (
            "HTTP Invalid Request Line"
        )  #
        BRIDGE_REACHABILITY = "bridge_reachability", (
            "Bridge Reachability"
        )  # need help
        TCP_CONNECT = "tcp_connect", ("TCP Connect")  #
        HTTP_HEADER_FIELD_MANIPULATION = "http_header_field_manipulation", (
            "HTTP header field manipulation"
        )  #
        HTTP_HOST = "http_host", ("HTTP host")  #
        MULTI_PROTOCOL_TRACEROUTE = "multi_protocol_traceroute", (
            "Multi-protocol Traceroute"
        )  # need help
        MEEK_FRONTED_REQUESTS_TEST = "meek_fronted_requests_test", (
            "Meek Frontend request test"
        )  #
        WHATSAPP = "whatsapp", ("Whatsapp")  #
        VANILLA_TOR = "vanilla_tor", ("Vanilla tor")  #
        FACEBOOK_MESSENGER = "facebook_messenger", ("Facebook Messenger")  #
        NDT = "ndt", ("NDT")
        DASH = "dash", ("DASH")
        TELEGRAM = "telegram", ("Telegram")  #
        PSIPHON = "psiphon", ("Psiphon")  #
        TOR = "tor", ("Tor")  #
        sni_blocking = "sni_blocking", ("SNI Blocking")  #
        UNKNOWN = "unknown", ("UNKNOWN")

    _DATABASE = "titan_db"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    input = models.TextField(null=True, db_index=True)
    annotations = JSONField()
    report_id = models.CharField(max_length=100)
    report_filename = models.CharField(max_length=250)
    options = models.TextField(null=True)
    probe_cc = models.CharField(max_length=50)
    probe_asn = models.CharField(max_length=50)
    probe_ip = models.GenericIPAddressField(null=True)
    data_format_version = models.CharField(max_length=100)
    test_name = models.CharField(max_length=60, choices=TestTypes.choices)
    test_start_time = models.DateTimeField(null=True)
    measurement_start_time = models.DateTimeField(db_index=True)
    test_runtime = models.FloatField(null=True)
    test_helpers = JSONField(blank=True, null=True)
    software_name = models.CharField(max_length=30)
    software_version = models.CharField(max_length=100)
    test_version = models.CharField(max_length=100)
    bucket_date = models.DateTimeField(null=True)
    # boolean created for post_save the raw_measurement
    is_processed = models.BooleanField(default=True)

    # ---------------------------------------------- #
    test_keys = JSONField()
    # This is the important part for the flags logic,
    # for every test type, there's specific data related to the
    # result for that test, and that data is stored in this json field
    # ---------------------------------------------- #


class Measurement(TimeStampedModel):
    """
    This model is an abstraction layer for
    the RawMeasurement model, which contains the information
    provided by ooni for each measurement. Our application
    logic will reside instead in this model.
    """

    # Measurement raw data
    raw_measurement = models.OneToOneField(
        to=RawMeasurement, on_delete=models.CASCADE, null=True
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)

    anomaly = models.BooleanField(default=False)

    domain = models.ForeignKey(to=Domain, null=True, on_delete=SET_NULL)

    asn = models.ForeignKey(to=ASN, null=True, on_delete=SET_NULL)

    def save(self, *args, **kwargs) -> None:

        # Get the url and check whether it is None or not
        url = self.raw_measurement.input
        if url is not None:
            # If not none, then get the domain and save it
            try:
                from vsf.utils import get_domain

                domain, _ = Domain.objects.get_or_create(
                    domain_name=get_domain(url), defaults={"site": None}
                )
                self.domain = domain
            except Exception as e:
                # If could not create this object, don't discard entire measurement, it's still important
                print(
                    f"Could not create domain for the following url: {url}. Error: {str(e)}",
                    file=sys.stderr,
                )

        asn = self.raw_measurement.probe_asn
        if asn is not None:
            try:
                asn, _ = ASN.objects.get_or_create(asn=str(asn))
                self.asn = asn
            except Exception as e:
                print(
                    f"Could not create asn for the following code: {asn}. Error: {str(e)}",
                    file=sys.stderr,
                )

        return super(Measurement, self).save(*args, **kwargs)
