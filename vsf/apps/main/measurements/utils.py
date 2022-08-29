# Django imports:
from django.db.models.query import QuerySet
from django.core.exceptions import FieldError
from django.db.models import Subquery, OuterRef

# Third party imports
import json
import requests
from typing import List

# Local imports
from .models import Measurement, RawMeasurement
import apps.main.measurements.submeasurements.models  as SubMeas

"""
    An experiment is a composition of several nettest + some additional
    logic or information.

    We provide links to the ooni spec where every experiment/nettest is
    specified.

    The experiments of major interest in this project are:
        - DNS Consistency   https://github.com/ooni/spec/blob/master/nettests/ts-002-dns-consistency.md
        - Web connectivity  https://github.com/ooni/spec/blob/master/nettests/ts-017-web-connectivity.md
        - TCP Connection

    The important nettest for these experiments are:
        - HTTP REQUEST  https://github.com/ooni/spec/blob/master/data-formats/df-001-httpt.md
        - DNS           https://github.com/ooni/spec/blob/master/data-formats/df-002-dnst.md
        - TCP CONNECT   https://github.com/ooni/spec/blob/master/data-formats/df-005-tcpconnect.md

    To check an experiment, we have to check its correspondig nettest and perform
    further examination based on the experiment itself

"""

def search_measurement_by_queryset(
        measurements  : QuerySet,
        since=None, until=None,
        test_name : str =None,
        ASN       : str =None,
        input     : str =None,
        site      : str =None,
        country   : str =None,
        anomaly   : bool=None,
        flags     : list=None
    ):
    """
        Given a QuerySet of Measurements x RawMeasurements, return a filtered
        version based on the given input. If Site argument is provided,
        site filtering wil only happen if the queryset provides the column 'site'.
    """
    if(since != None and since != ""):
        measurements = measurements.filter(raw_measurement__measurement_start_time__gte=since)
    if(until != None and until != ""):
        measurements = measurements.filter(raw_measurement__measurement_start_time__lte=until)
    if (test_name != None and test_name != ""):
        measurements = measurements.filter(raw_measurement__test_name=test_name)
    if (ASN != None and ASN != ""):
        measurements = measurements.filter(raw_measurement__probe_asn=ASN)
    if (input != None and input != ""):
        measurements = measurements.filter(raw_measurement__input__contains=input)
    if (anomaly != None and anomaly != ""):
        measurements = measurements.filter(anomaly=anomaly)
    if flags:
        measurements = _filter_by_flag_no_ok(measurements, flags)

    measurements.site = None
    if site != None and site != "":
        try:
            measurements = measurements.filter(domain__site=site)
        except FieldError:
            pass

    return measurements

def get_measurement_from_ooni(id : str) -> RawMeasurement:
    """
        This is a test utility function, it is not intended to be present
        in some production logic (for now). Use it to store measurements
        from ooni easier
    """
    # for testing:
    # from  apps.main.measurements.utils import get_measurement_from_ooni
    measurement_url = "https://api.ooni.io/api/v1/measurement/{}".format(id)
    # you can test with this measurement https://api.ooni.io/api/v1/temp-id-444701864
    req = requests.get(measurement_url)

    if req.status_code != 200:
        return None

    data = req.json()

    new_meas = RawMeasurement(
            test_keys       =data['test_keys'],
            test_start_time =data['test_start_time'],
            probe_ip        =data['probe_ip'],
            id              =data['id'],
            test_helpers    =data['test_helpers'],
            probe_cc        =data['probe_cc'],
            test_runtime    =data['test_runtime'],
            input           =data['input'],
            probe_asn       =data['probe_asn'],
            annotations     =data['annotations'],
            software_name   =data['software_name'],
            software_version=data['software_version'],
            data_format_version=data['data_format_version'],
            report_filename =data['report_filename'],
            test_version    =data['test_version'],
            bucket_date     =data['bucket_date'],
            test_name       =data['test_name'],
            report_id       =data['report_id'],
            measurement_start_time=data['measurement_start_time'],
            options         =data['options']
        )

    new_meas.save()


def anomaly(measurement : RawMeasurement) -> bool:
    """
        This function checks if the given measurement
        presents some kind of anomaly, it depends on the
        measurement type (test_name).

        Input:
            measurement: The RawMeasurement object to check for anomalies

        Output:
            If the measurement presents some kind of anomaly
    """
    test_name = measurement.test_name
    types = RawMeasurement.TestTypes

    if test_name == types.WEB_CONNECTIVITY:
        return anomaly_web_conn(measurement)
    elif test_name == types.DNS_CONSISTENCY:
        return anomaly_dns_cons(measurement)
    elif test_name == types.WHATSAPP:
        return anomaly_WA(measurement)
    elif test_name == types.TELEGRAM:
        return anomaly_telegram(measurement)
    elif test_name == types.PSIPHON:
        return anomaly_psiphon(measurement)
    elif test_name == types.FACEBOOK_MESSENGER:
        return anomaly_fb(measurement)
    elif test_name == types.TOR:
        return anomaly_tor(measurement)
    elif test_name == types.TCP_CONNECT:
        return anomaly_tcp(measurement)
    elif test_name == types.VANILLA_TOR:
        return anomaly_vanilla_tor(measurement)
    elif test_name == types.HTTP_HEADER_FIELD_MANIPULATION:
        return anomaly_http_headers(measurement)
    elif test_name == types.HTTP_INVALID_REQUEST_LINE:
        return anomaly_invalid_request(measurement)
    elif test_name == types.MEEK_FRONTED_REQUESTS_TEST:
        return anomaly_meek_request(measurement)
    elif test_name == types.sni_blocking:
        return anomaly_SNI(measurement)

    assert False, f"Unknown type of submeasurement '{test_name}'"


def anomaly_web_conn(measurement : RawMeasurement) -> bool:
    """
        This function checks if a RawMeasurement of type "web_connectivity"
        presents some kind of anomaly. It may raise an error if the measurement is not
        a web_conn
    """

    blocking = measurement.test_keys['blocking']
    block_states = ['tcp_ip', 'dns', 'http-failure', 'http-diff']

    #Note that some fields may be null-boolean
    return  blocking in block_states or\
            measurement.test_keys['dns_consistency'] == 'inconsistent' or\
            not measurement.test_keys['title_match'] or\
            not measurement.test_keys['body_length_match'] or\
            not measurement.test_keys['headers_match'] or\
            not measurement.test_keys['status_code_match']

def anomaly_dns_cons(measurement : RawMeasurement) -> bool:
    """
        This function checks if a RawMeasurement of type "dns_consistency" is
        actually consistent. It may raise an error if the measurement is not a dns_consistency
    """

    inconsistent = measurement.test_keys['inconsistent']

    return len(inconsistent) != 0

def anomaly_WA(measurement : RawMeasurement) -> bool:
    """
        This function checks if a RawMaasurement of type "whatsapp" presents some kind of anomaly.
        It may raise an error if the given measurement is not a "whatsapp" test
    """

    test_keys = measurement.test_keys
    reg_server_status = test_keys['registration_server_status']
    endpoints_status  = test_keys['whatsapp_endpoints_status']
    web_status        = test_keys['whatsapp_web_status']

    return reg_server_status != 'ok' or endpoints_status != 'ok' or web_status != 'ok'

def anomaly_telegram(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type "telegram" is consistent.
        It may raise an error if the measurement is not a dns_consistency
    """

    test_keys = measurement.test_keys

    http_block = test_keys['telegram_http_blocking']
    tcp_block  = test_keys['telegram_tcp_blocking']
    web_status = test_keys['telegram_web_status']

    return http_block or tcp_block or web_status == "blocked"

def anomaly_psiphon(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type "psiphon" presents some kind of
        anomaly. Anomalies considered:
        "error using psiphon"
        "error bootstrapping psiphon"
    """
    test_keys = measurement.test_keys
    failure = test_keys['failure']
    bs_time = test_keys.get('bootstrap_time') or 0

    return bs_time == 0 or failure != None


def anomaly_http_host(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type 'http_host' presents
        some kind of anomaly
        TODO: revisar esto con andres
    """

    test_keys = measurement.test_keys
    fuzzy_matching = test_keys.get('filtering_via_fuzzy_matching')
    new_line       = test_keys.get('filtering_prepend_newline_to_method')
    tab_to_host    = test_keys.get('filtering_add_tab_to_host')
    subdomain      = test_keys.get('filtering_of_subdomain')

    return fuzzy_matching or new_line or tab_to_host or subdomain

def anomaly_http_requests(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type "http_requests" presents
        some kind of anomaly
        TODO: revisar esto con andres
    """
    return measurement.test_keys.get('body_length_match') != True # it may be true, false or none

def anomaly_tcp(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type "tcp_connect" presents
        some kind of anomaly
    """

    return measurement.test_keys['connection'] == 'success'

def anomaly_fb(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type 'facebook_messenger' presents some kind of
        anomaly
    """

    test_keys = measurement.test_keys
    dns_block = test_keys.get("facebook_dns_blocking") or False
    tcp_block = test_keys.get("facebook_tcp_blocking") or False

    return dns_block or tcp_block

def anomaly_tor(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type 'tor' presents
        some kind of anomaly
        TODO: Revisar esto con andres
    """
    test_keys = measurement.test_keys
    dir_port_total      = test_keys.get('dir_port_total') or 0
    dir_port_accessible = test_keys.get('dir_port_accessible') or 0

    obfs4_total = test_keys.get('obfs4_total') or 0
    obfs4_accessible = test_keys.get('obfs4_accessible') or 0

    or_port_dirauth_total = test_keys.get('or_port_dirauth_total')
    or_port_dirauth_accessible = test_keys.get('or_port_dirauth_accessible')

    or_port_total = test_keys.get('or_port_total') or 0
    or_port_accessible = test_keys.get('or_port_accessible') or 0

    return  dir_port_total != dir_port_accessible or\
            obfs4_total != obfs4_accessible or\
            or_port_dirauth_total != or_port_dirauth_accessible or\
            or_port_total != or_port_accessible

def anomaly_vanilla_tor(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type 'vanilla_tor' presents
        some kind of anomaly. Note that if this measurement
        says that it has no anomalies, it may mean that
        it was not able to conclude anything at all.
    """

    success = measurement.test_keys.get('success') or True

    return not success

def anomaly_http_headers(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type 'vanilla_tor' presents some kind
        of anomaly
    """

    return measurement.test_keys.get('total') or False

def anomaly_invalid_request(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type 'http_invalid_request_line' presents
        some kind of anomaly
    """

    return measurement.test_keys.get('tampering') or False

def anomaly_meek_request(measurement : RawMeasurement) -> bool:
    """
        Checks if a Raw measurement of type 'meek_fronted_requests_test' presents
        some kind of anomaly
        TODO: revisar con andres
    """
    return not measurement.test_keys['success']

def anomaly_SNI(measurement : RawMeasurement) -> bool:
    """
        Checks if a RawMeasurement of type 'sni_blocking' presents
        some kind of anomaly
        TODO: revisar con andrés, actualmente considero también como
        anomalía los que están marcados con 'anomaly.*', pero no sé
        si esos sean errores interesantes
    """

    return measurement.test_keys['result'] != 'success.got_server_hello'

def _filter_by_flag_no_ok(qs : QuerySet, subm_to_filter : List[str]) -> QuerySet:
    """
    Summary:
        Given a queryset and a list of str with submeasurement names, return a queryset such that
        every instance has a submeasurement such that its flag is not ok
    Params:
        qs : QuerySet = Measurement Queryset to filter
        subm_to_filter : List[str] = list of submeasurement names, not case sensitive
    Return:
        QuerySet = Filtered queryset. If the given list is empty, the same queryset is returned.
    """
    # Check that this is a Measurement QuerySet
    assert qs.model == Measurement, "This queryset is not a Measurement QuerySet"

    # If nothing to filter, return the same queryset
    if not subm_to_filter: return qs

    def filter_aux(subm_type, qs : QuerySet) -> QuerySet:
        field_name = f"{subm_type.__name__}_flag"
        sq = subm_type.objects.filter(measurement=OuterRef('pk')).exclude(flag_type=SubMeas.SubMeasurement.FlagType.OK)
        return qs.annotate(**{field_name:Subquery(sq[:1].values('flag_type'))}).exclude(**{field_name:None})

    lowered_list = [s.lower() for s in subm_to_filter]
    qs1, qs2, qs3 = None, None, None
    if 'dns' in lowered_list:
        qs1 = filter_aux(SubMeas.DNS, qs)
    
    if 'http' in lowered_list:
        qs2 = filter_aux(SubMeas.HTTP, qs)
    
    if 'tcp' in lowered_list:
        qs3 = filter_aux(SubMeas.TCP, qs)

    qsFinal = None
    if qs1 and not qsFinal: qsFinal = qs1 
    if qs2 and not qsFinal: qsFinal = qs2 
    if qs2 and qsFinal:  qsFinal = qsFinal | qs2 
    if qs3 and not qsFinal: qsFinal = qs3
    if qs3 and qsFinal:  qsFinal = qsFinal | qs3 

    if qsFinal: return qsFinal
    else: return qs