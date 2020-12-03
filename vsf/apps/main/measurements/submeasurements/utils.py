
# @TODO we have to refactor this file, it's too big


# Django imports 
from django.core.paginator               import Paginator

# Local imports
from .models                             import DNS, DNSJsonFields, HTTP, TCP, SubMeasurement
from apps.main.measurements.models       import RawMeasurement, Measurement
from apps.main.measurements.flags.models import Flag

# -- SubMeasurement Creation -------------------------------------------------------+

def createSubMeasurements(measurement : RawMeasurement) -> [SubMeasurement]:
    """
        Creates a new list of submeasurements based on a RawMeasurement
    """

    if measurement.test_name == RawMeasurement.TestTypes.WEB_CONNECTIVITY :

        dns  = [meas for meas in createDNSFromWebConn(measurement) if meas != None] 
        tcp  = [meas for meas in createTCPFromWebCon(measurement) if meas != None]
        http = createHTTPFromWebCon(measurement)
        http = [http] if http != None else []

        return dns + tcp + http
        
    elif measurement.test_name == RawMeasurement.TestTypes.DNS_CONSISTENCY :
        return createDNSFromDNSCons(measurement)

    return []

def createDNSFromWebConn(web_con_measurement : RawMeasurement) -> [DNS]:
    """
        Each type of measurement requires a totally different way to create
        its sub measurements. This function creates a DNS submeasurement
        given a web_connectivity measurement. 
        Note that the Measurement field is not provided since it may not be created yet.
        Set this field manually to a valid Measurement.
    """

    # Sanity & consistency check: See if the measurement is a web_connectivity measurement
    if web_con_measurement.test_name != RawMeasurement.TestTypes.WEB_CONNECTIVITY:
        raise AttributeError("The given measurement is not a web_connectivity measurement")

    # Get the relevant data to build this measurement
    test_keys = web_con_measurement.test_keys

    queries                 = test_keys['queries']
    control_resolver        = test_keys['control']
    dns_consistency         = test_keys['dns_consistency']
    dns_experiment_failure  = test_keys['dns_experiment_failure']

    cr = {} # control resolver information
    try:
        cr['failure'] = control_resolver['dns']['failure']
    except:
        cr['failure'] = None

    try:
        cr['answers'] = {
            'addrs': control_resolver['dns']['addrs']
        }
    except Exception:
            cr['answers'] = None

    new_dns = []
    for query in queries:

        # Check query consistency
        inconsistent = None # dns_consistency == 'reverse_match'
        if dns_consistency == 'consistent':
            inconsistent = False
        elif dns_consistency == 'inconsistent':
            inconsistent = True
        jsonf = DNSJsonFields.objects.create(answers=query['answers'],control_resolver_answers=cr['answers'])        
        dns = DNS(
            measurement=None,
            flag=None,
            control_resolver_failure=cr['failure'],
            failure=dns_experiment_failure,
            hostname=query['hostname'],
            dns_consistency= dns_consistency,
            inconsistent= inconsistent,
            jsons=jsonf
        )
        new_dns.append(dns)

    return new_dns

def createDNSFromDNSCons(measurement : RawMeasurement) -> [DNS]:
    """
        This function creates a DNS measurement based on a DNS consistency test
        PENDIENTE POR REVISAR:
        No pude conseguir una medición de prueba para probar esta función, está 
        pendiente testearla. Por ahora solo es copy paste de la versión del sistema viejo
    """
    # Get the relevant data
    test_keys = measurement.test_keys
    queries             = test_keys['queries']
    inconsistent        = test_keys['inconsistent']
    errors              = test_keys['errors']
    failures            = test_keys['failures']
    control_resolver    = test_keys['control']

    new_dns : [DNS] = []
    # Control resolver ip addres:
    cr_ip = control_resolver.split(":")[0]
    # Control resolver data:
    cr = {}
    for query in queries:
        # Look for the control resolver
        if (
                query['resolver_hostname'] == cr_ip and
                measurement.input == query['hostname']
            ):
                cr['failure'] = query['failure']
                cr['answers'] = query['answers']
                cr['resolver_hostname'] = query['resolver_hostname']

    for query in queries:
        if (    query['resolver_hostname'] != cr_ip and
                query['query_type'] == 'A' ):
            domain = measurement.input
            is_inconsistent = None
            dns_consistency = ''
            if query['resolver_hostname'] in inconsistent:
                is_inconsistent = True
                dns_consistency = 'inconsistent responses'
            else:
                try:
                    if (
                        errors[query['resolver_hostname']] == 'no_answer'
                        and
                        not (
                            (control_resolver in errors)
                            or cr['failure']
                            or control_resolver in failures
                        )
                    ):
                        is_inconsistent = True
                        dns_consistency = 'no_answer'
                    elif (
                        errors[query['resolver_hostname']] == 'reverse_match'
                        and
                        not(
                            (control_resolver in errors)
                            or cr['failure']
                            or control_resolver in failures
                        )):
                        is_inconsistent=False
                        dns_consistency = 'reverse_match'

                    else:
                        dns_consistency = 'consitent if exists'
                        is_inconsistent = False
                        try:
                            dns_consistency = errors[query['resolver_hostname']] + '(Resolver)'
                        except:
                            pass
                except KeyError:
                    is_inconsistent = False
                except:
                        pass
                
                jsonf = DNSJsonFields.objects.create(answers=query['answers'], control_resolver_answers=cr['answers'])
                if dns_consistency:
                    dns = DNS(
                        measurement=None,
                        control_resolver_failure=cr['failure'],
                        control_resolver_hostname=cr['resolver_hostname'],
                        failure=query['failure'],
                        resolver_hostname=query['resolver_hostname'],
                        dns_consistency=dns_consistency,
                        inconsistent=is_inconsistent,
                        hostname=query['hostname'],
                        jsons=jsonf
                    )

                else:
                    dns = DNS(
                        measurement=None,
                        control_resolver_failure=cr['failure'],
                        control_resolver_hostname=cr['resolver_hostname'],
                        failure=query['failure'],
                        resolver_hostname=query['resolver_hostname'],
                        dns_consistency=dns_consistency,
                        hostname=query['hostname'],
                        jsons=jsonf
                    )

                new_dns.append(dns)

    return new_dns


def createHTTPFromWebCon(measurement : RawMeasurement) -> HTTP:
    """
        This function creates an HTTP submeasurement based
        on a measurement. This is necesary for creating the 
        submeasurements related to a single measurment. 
        Note that this function may return None in some cases, 
        when the measurement is meaningless due to an HTTP test 
        failure.
    """

    test_keys           = measurement.test_keys
    # Get relevant data from test_keys
    status_code_match   = test_keys['status_code_match']
    headers_match       = test_keys['headers_match']
    body_length_match   = test_keys['body_length_match']
    body_proportion     = test_keys['body_proportion']

    # There's some cases where the measurement is not valuable, 
    # for example when the experiment failed to connect,
    # in those cases the body_length_match is set tu null (None), 
    # and so other fields
    if     (status_code_match  is not None) and (
            body_length_match  is not None) and (
            headers_match      is not None) and (
            body_proportion    is not None):
        
        http = HTTP(
            measurement=None,
            status_code_match=status_code_match,
            headers_match=headers_match,
            body_length_match=body_length_match,
            body_proportion=body_proportion,
        )
        return http
    
    return None

def createTCPFromWebCon(measurement : RawMeasurement) -> [TCP]:
    """
        Create a TCP test sub measurement from a web_connectivity measurement
    """
    test_keys = measurement.test_keys

    tcp_connect = test_keys["tcp_connect"]

    new_tcp = []
    for tcp_connect_item in tcp_connect:
        try:
            if  (tcp_connect_item['status']['blocked'] is not None) and (
                (tcp_connect_item['status']['success'] is not None)):
                new_tcp.append (TCP(
                    measurement=None,
                    flag=None,
                    status_blocked=tcp_connect_item['status']['blocked'],
                    status_failure=tcp_connect_item['status']['failure'],
                    status_success=tcp_connect_item['status']['success'],
                    ip=tcp_connect_item['ip']
                ))
        except:
            pass

    return new_tcp

# -- Flag Checking -------------------------------------------------------+

def SoftFlag(since=None, until=None, limit : int = None, page_size : int = 1000, absolute : bool = False):
    """
        This function Flags every measurement from the start time 
        "since" to "until".  if some of them is not provided, 
        take the highest/lowest possible bound.

        You can limit the number of considered measurements by providing a "limit" number,
        the maximum ammount of measurements to check per measurement type. 
        
        "Absolute" means that every measurement will be considered, even if it is already checked.
        Use with aution

        "page_size" means the size of the page while paginating the query
    """

    # Argument checker
    assert isinstance(page_size, int), "Limit argument should be an integer number"
    assert page_size > 0, "Limit argument should be a positive number"

    meas_types = [DNS, TCP, HTTP]

    tagged = 0
    not_tagged = 0
    for MS in meas_types:
        measurements = MS.objects.all()\
                            .select_related('measurement', 'measurement__raw_measurement', 'flag')\
        
        # Apply optional filtering
        if until:
            measurements = measurements.filter(measurement__raw_measurement__measurement_start_time__lt = until)
        if since:
            measurements = measurements.filter(measurement__raw_measurement__measurement_start_time__gt = since) 
        if not absolute:
            measurements = measurements.filter(flag = None)

        measurements = measurements.order_by('measurement')
        
        if limit and limit > 0:
            measurements = measurements[:limit]


        # Apply pagination
        paginator = Paginator(measurements, page_size)
        
        for i in paginator.page_range:
            page = paginator.page(i)
            for m in page:
                if check_submeasurement(m):
                    new_flag = Flag.objects.create(flag = Flag.FlagType.SOFT) # create a new flag
                    m.flag = new_flag   # set the new flag
                    m.save()            # Store the measurement
                    tagged += 1         # annotate the saved objects
                else:
                    new_flag = Flag.objects.create(flag = Flag.FlagType.OK) # create a new flag
                    m.flag = new_flag       # set the new flag
                    m.save()                # Store the measurement
                    not_tagged += 1    # annotate the saved objects

            del page

    return {
            'tagged':tagged, 
            'not_tagged':not_tagged, 
        }
        

def check_submeasurement(submeasurement : SubMeasurement) -> bool:
    """
        Shortcut function to check if a submeasurement should be tagget 
        with a soft flag
    """
    if isinstance(submeasurement, TCP):
        return check_tcp(submeasurement)
    elif isinstance(submeasurement, HTTP):
        return check_http(submeasurement)
    elif isinstance(submeasurement, DNS):
        return check_dns(submeasurement)

    return False

def check_dns(dns : DNS) -> bool:
    """
        Checks if the given sub measurement of type DNS should have a soft flag
    """

    types = RawMeasurement.TestTypes
    dnsType = dns.measurement.raw_measurement.test_name

    if dnsType == types.DNS_CONSISTENCY:
        return check_dns_from_dns_cons(dns)
    elif dnsType == types.WEB_CONNECTIVITY:
        return check_dns_from_web_conn(dns)
    else:
        raise AttributeError(
            "The given measurement is not a valid DNS parent measurement or is not yet supported." +
            "\nGiven: ", dnsType
        )
    

def check_dns_from_web_conn(dns : DNS) -> bool:
    """
        Checks if the given sub_measurement of type DNS should have a flag.
        This function asserts that the measurements type is 
        web_connectivity.
    """
    return  dns.inconsistent or\
            (   
                dns.inconsistent == False and\
                dns.failure == "no_answer"
            )

def check_dns_from_dns_cons(dns : DNS) -> bool:
    """
        Checks if the given submeasurement of type DNS should have a soft flag. 
        This function asserts that the measurement type is dns_consistency
    """
    if dns.inconsistent:
        return True
    
    if  dns.control_resolver_failure not in [None, ''] or\
        dns.failure not in [None, ''] or\
        not dns.control_resolver_answers:
        return False

    return  dns.\
            measurement.\
            raw_measurement.\
            test_keys.get('errors', default={}).\
            get(dns.resolver_hostname) == "no_answer"

def check_http(http : HTTP, body_proportion_limit : float = 1.0) -> bool:
    """
        Checks if the given submeasurement of type DNS should have a soft flag.
        param: http = The HTTP submeasurement to check
        param: body_proportion_limit = A tolerance ratio to accept a http_measurement as
        invalid
    """
    return (not http.headers_match and\
            not http.body_length_match or\
            not http.status_code_match) or\
            http.body_proportion < body_proportion_limit 

def check_tcp(tcp : TCP) -> bool:
    """
        Checks if the given submeasurement of type DNS Ssho
    """

    return tcp.status_blocked 

# @TODO format later
from .FlagsUtils import count_flags, hard_flag