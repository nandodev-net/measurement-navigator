"""
    Additional functionality to perform validations in the post request
"""

from rest_framework.response    import Response
from rest_framework.generics    import  (
    ListCreateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.status      import  (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_412_PRECONDITION_FAILED
)
import django.utils.timezone    as timezone
import django.utils.dateparse   as dateparse
from   django.shortcuts         import render
from   rest_framework.views     import APIView
from   django.core.cache        import cache

# Third party imports
import sys
import time
import json
import requests
import datetime
import collections
from urllib.parse   import urlencode

# Local imports
from apps.main.sites.models             import URL
from apps.main.asns.models              import ASN
from .                                  import utils
from apps.main.ooni_fp.fp_tables.models import FastPath
from apps.main.measurements.models      import RawMeasurement

def checkPostData(data) -> bool:
        """
        This function will check if the input data on the post request is valid.
        The input data should contain:
            since: measurement since this date (date in string format)
            until: measurement until this date (date in string format)
            probe_cc: 2 chars country code

        The dates are expected to be in the following format: YYYY-mm-dd
        """

        # Check valid input
        if not isinstance(data, collections.Mapping):
            raise  TypeError('Data parameter in checkPostData should be a Mapping type object')

        since = data.get('since')
        until = data.get('until')
        probe_cc = data.get('probe_cc')

        # Check if every field is a string
        if (not isinstance(since, str)) or (not isinstance(until,str)) or (not isinstance(probe_cc,str)):
            print("bad types")
            return False

        # Check valid fields
        if (since == None) or (until == None) or (probe_cc == None):
            return False

        date_format = '%Y-%m-%d'
        # check date formats
        try:
            datetime.datetime.strptime(since, date_format)
        except:
            return False

        try:
            datetime.datetime.strptime(until, date_format)
        except:
            return False

        # Check country code has 2 chars & uppercase (ooni requires it to be upper)
        if len(probe_cc) != 2 or not probe_cc.isupper():
            # Warning: It's still possible that the country code is not valid,
            # further validation will be performed during the database queryng
            return False


        return True

def request_fp_data(test_name: str, since: str, until: str, from_fastpath: bool = True, limit:int =None) -> (int, [str]):
    """
        Given the start and end date for a set of measurements,
        perform a get request to ooni in order to get the
        recent fast path objects and store them in the database.

        The function returns the status code for the ooni request
        and a list of tid corresponding to the actually added measurements.

        'from_fastpath' param remains unused for now, we need this in the first place
        to recover not-ready measurements, but that concept seems to be gone. 

        'limit' param provides a limit for the maximum ammount of stored measurements

        both the since and until date should be in the following format:
        YYYY-mm-dd.
    """

    day_time_ini = time.time()

    web_con = False
    tor = False
    http_requests = False
    dns_consistency = False
    http_invalid_request_line = False
    bridge_reachability = False
    tcp_connect = False
    http_header_field_manipulation = False
    http_host = False
    multi_protocol_traceroute = False
    meek_fronted_requests_test = False
    whatsapp = False
    vanilla_tor = False
    facebook_messenger = False
    ndt = False
    dash = False
    telegram = False
    psiphon = False
    sni_blocking = False   

    page_req = False

    meas_req_wc = False
    meas_req_tr = False
    meas_req_http_requests = False
    meas_req_dns_consistency = False
    meas_req_http_invalid_request_line = False
    meas_req_bridge_reachability = False
    meas_req_tcp_connect = False
    meas_req_http_header_field_manipulation = False
    meas_req_http_host = False
    meas_req_multi_protocol_traceroute = False
    meas_req_meek_fronted_requests_test = False
    meas_req_whatsapp = False
    meas_req_vanilla_tor = False
    meas_req_facebook_messenger = False
    meas_req_ndt = False
    meas_req_dash = False
    meas_req_telegram = False
    meas_req_psiphon = False
    meas_req_sni_blocking = False  

    f = open( 'informe0.txt', 'w')
    f.write('INICIANDO DIAGNOSTICO ')
    f.write(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    f.write('\n')
    
   
    # Data validation
    data = {
        'probe_cc': 'VE', # In case we want to add other countries
        'since': since,
        'until': until,
        'limit': 100,
        'order':'asc',
        'order_by' : 'measurement_start_time',
        'input': 'http://partidounnuevotiempo.org/'
    }

    if test_name:
        data['test_name'] = test_name

    # Check if the post data is valid:
    if not checkPostData(data):
        raise AttributeError("Unvalid input arguments. Given: \n" +
                                "   Since: " + since + "\n" +
                                "   Until: " + until)

    # Perform a get request from Ooni
    next_url = 'https://api.ooni.io/api/v1/measurements?' + urlencode(data)
    from vsf.utils import Colors as c
    print(c.magenta("\n\nRequesting URL: \n"), next_url)

    # We store the earliest measurement so we can update just what needs to be updated 
    # when computing hard flags and updating measurement count
    cache_min_date = datetime.datetime.now() + datetime.timedelta(days=1)

    objects = [] # List of measurement objects obtained
    status_code = 200

    while next_url != None:
        try:
            # If it wasn't able to get the next page data, just store the currently added data
            # @TODO we have to think what to do in this cases
            pag_ini = time.time()
            req = requests.get(next_url)
            pag_fin = time.time()
        
            if not page_req:
                f.write('Tiempo en request a ooni de una pagina de 100 mediciones parciales: ')
                f.write(str(pag_fin-pag_ini))
                f.write('\n')
                page_req = True
 
            status_code = req.status_code
            assert(req.status_code == 200)
        except:
            break

        # Since everything went ok, we get the data in json format
        data = req.json()
        metadata = data['metadata']
        next_url = metadata.get('next_url')
        if from_fastpath:
            results = filter(
            # since we just care about fast path data, we filter the ones whose measurement_id begins with
            # 'temp-fid' according to what Federico (from ooni) told us
            # UPDATE: by today, measurement_id is not reported by the ooni queries, so
            # we can't rely on it to check whether a measurement comes from the fastpath or not.
            # @TODO
            lambda res:
                    res.get('measurement_id',"").startswith("temp-fid"),
                data['results']
            )
        else:
            results = data['results']

        # for result in results:
        #     print(c.green('Creating FastPath Meas'), result['report_id'])
        #     fp = FastPath(
        #         anomaly = result['anomaly'],
        #         confirmed = result['confirmed'],
        #         failure = result['failure'],
        #         input= str(result['input']),
        #         tid= result.get('measurement_id'),
        #         measurement_start_time=result['measurement_start_time'],
        #         measurement_url=result['measurement_url'],
        #         probe_asn= result['probe_asn'],
        #         probe_cc= result['probe_cc'],
        #         report_id= result['report_id'],
        #         scores=result['scores'],
        #         test_name= result['test_name'],
        #     )
        #     URL.objects.get_or_create(url=fp.input)
        #     objects.append(fp)
        
        for result in results:
            URL.objects.get_or_create(url=str(result['input']))
            if result['test_name'] == 'tor':
                URL.objects.get_or_create(url='tor')
            try:
                meas_ini = time.time()
                req = requests.get(result['measurement_url'])
                meas_fin = time.time()
                if result['test_name'] == 'tor' and not meas_req_tr:
                    f.write('Tiempo en request a ooni de una medicion TOR: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_tr = True
                elif result['test_name'] == 'web_connectivity' and not meas_req_wc:
                    f.write('Tiempo en request a ooni de una medicion WebConn: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_wc = True
                elif result['test_name'] == 'http_requests' and not meas_req_http_requests:
                    f.write('Tiempo en request a ooni de una medicion http_requests: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_http_requests = True  
                elif result['test_name'] == 'dns_consistency' and not meas_req_dns_consistency:
                    f.write('Tiempo en request a ooni de una medicion dns_consistency: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_dns_consistency = True  
                elif result['test_name'] == 'http_invalid_request_line' and not meas_req_http_invalid_request_line:
                    f.write('Tiempo en request a ooni de una medicion http_invalid_request_line: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_http_invalid_request_line = True 
                elif result['test_name'] == 'bridge_reachability' and not meas_req_bridge_reachability:
                    f.write('Tiempo en request a ooni de una medicion bridge_reachability: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_bridge_reachability = True 
                elif result['test_name'] == 'tcp_connect' and not meas_req_tcp_connect:
                    f.write('Tiempo en request a ooni de una medicion tcp_connect: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_tcp_connect = True 
                elif result['test_name'] == 'http_header_field_manipulation' and not meas_req_http_header_field_manipulation:
                    f.write('Tiempo en request a ooni de una medicion http_header_field_manipulation: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_http_header_field_manipulation = True 
                elif result['test_name'] == 'http_host' and not meas_req_http_host:
                    f.write('Tiempo en request a ooni de una medicion http_host: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_http_host = True 
                elif result['test_name'] == 'multi_protocol_traceroute' and not meas_req_multi_protocol_traceroute:
                    f.write('Tiempo en request a ooni de una medicion multi_protocol_traceroute: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_multi_protocol_traceroute = True 
                elif result['test_name'] == 'meek_fronted_requests_test' and not meas_req_meek_fronted_requests_test:
                    f.write('Tiempo en request a ooni de una medicion meek_fronted_requests_test: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_meek_fronted_requests_test = True 
                elif result['test_name'] == 'whatsapp' and not meas_req_whatsapp:
                    f.write('Tiempo en request a ooni de una medicion whatsapp: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_whatsapp = True
                elif result['test_name'] == 'vanilla_tor' and not meas_req_vanilla_tor:
                    f.write('Tiempo en request a ooni de una medicion vanilla_tor: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_vanilla_tor = True
                elif result['test_name'] == 'facebook_messenger' and not meas_req_facebook_messenger:
                    f.write('Tiempo en request a ooni de una medicion facebook_messenger: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_facebook_messenger = True
                elif result['test_name'] == 'ndt' and not meas_req_ndt:
                    f.write('Tiempo en request a ooni de una medicion ndt: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_ndt = True
                elif result['test_name'] == 'dash' and not meas_req_dash:
                    f.write('Tiempo en request a ooni de una medicion dash: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_dash = True
                elif result['test_name'] == 'telegram' and not meas_req_telegram:
                    f.write('Tiempo en request a ooni de una medicion telegram: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_telegram = True
                elif result['test_name'] == 'psiphon' and not meas_req_psiphon:
                    f.write('Tiempo en request a ooni de una medicion psiphon: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_psiphon = True
                elif result['test_name'] == 'sni_blocking' and not meas_req_sni_blocking:
                    f.write('Tiempo en request a ooni de una medicion sni_blocking: ')
                    f.write(str(meas_fin-meas_ini))
                    f.write('\n')
                    meas_req_sni_blocking = True

                status_code = req.status_code
                assert req.status_code == 200
            except:
                continue
    

    # Save only if this measurement does not exists
    # saved_measurements = []
    # for fp in objects:
    #     try:
    #         fp_old = FastPath.objects.get(
    #                     measurement_start_time=fp.measurement_start_time,
    #                     input=fp.input,
    #                     report_id=fp.report_id,
    #                     test_name=fp.test_name)
    #         continue
    #     except FastPath.DoesNotExist:
    #         pass

        #Since this measurement is not yet stored, try to recover its complete data if possible
        # try:
        #     req = requests.get(fp.measurement_url)
        #     status_code = req.status_code
        #     assert req.status_code == 200
        # except:
        #     fp.save()
        #     saved_measurements.append(fp.id)
        #     continue


            from vsf.utils import Colors as c
            try:
                print(c.magenta("Creating a new measurement"))
                data = req.json()
                if data['test_name'] == 'tor':
                    input_ = 'tor'
                else:
                    input_ = data['input'] 
                meas_cr_ini = time.time()
                ms = RawMeasurement.objects.create(
                    input=input_,
                    report_id= data['report_id'],
                    report_filename= data.get('report_filename','NO_AVAILABLE'), #
                    options= data.get('options', "NO_AVAILABLE"), #
                    probe_cc= data.get('probe_cc','VE'),
                    probe_asn= data['probe_asn'],
                    probe_ip=data.get('probe_ip'),
                    data_format_version= data['data_format_version'],
                    test_name= data['test_name'],
                    test_start_time= data.get('test_start_time'),
                    measurement_start_time= data['measurement_start_time'],
                    test_runtime= data.get('test_runtime'),
                    test_helpers= data.get('test_helpers',"NO_AVAILABLE"),
                    software_name= data['software_name'],
                    software_version= data['software_version'],
                    test_version= data['test_version'],
                    bucket_date= data.get('bucket_date'), #
                    test_keys= data['test_keys'],
                    annotations= data['annotations']
                )
                meas_cr_fin = time.time()
                if data['test_name'] == 'tor' and not tor:
                    f.write('Tiempo en creacion medicion TOR: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    tor = True
                elif data['test_name'] == 'web_connectivity' and not web_con:
                    f.write('Tiempo en creacion medicion WebConn: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    web_con = True  
                elif result['test_name'] == 'http_requests' and not http_requests:
                    f.write('Tiempo en creacion medicion http_requests: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    http_requests = True  
                elif result['test_name'] == 'dns_consistency' and not dns_consistency:
                    f.write('Tiempo en creacion medicion dns_consistency: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    dns_consistency = True  
                elif result['test_name'] == 'http_invalid_request_line' and not http_invalid_request_line:
                    f.write('Tiempo en creacion medicion http_invalid_request_line: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    http_invalid_request_line = True 
                elif result['test_name'] == 'bridge_reachability' and not bridge_reachability:
                    f.write('Tiempo en creacion medicion bridge_reachability: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    bridge_reachability = True 
                elif result['test_name'] == 'tcp_connect' and not tcp_connect:
                    f.write('Tiempo en creacion medicion tcp_connect: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    tcp_connect = True 
                elif result['test_name'] == 'tcp_connect' and not tcp_connect:
                    f.write('Tiempo en creacion medicion tcp_connect: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    tcp_connect = True 
                elif result['test_name'] == 'http_header_field_manipulation' and not http_header_field_manipulation:
                    f.write('Tiempo en creacion medicion http_header_field_manipulation: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    http_header_field_manipulation = True 
                elif result['test_name'] == 'http_host' and not http_host:
                    f.write('Tiempo en creacion medicion http_host: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    http_host = True 
                elif result['test_name'] == 'multi_protocol_traceroute' and not multi_protocol_traceroute:
                    f.write('Tiempo en creacion medicion multi_protocol_traceroute: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    multi_protocol_traceroute = True 
                elif result['test_name'] == 'meek_fronted_requests_test' and not meek_fronted_requests_test:
                    f.write('Tiempo en creacion medicion meek_fronted_requests_test: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    meek_fronted_requests_test = True 
                elif result['test_name'] == 'whatsapp' and not whatsapp:
                    f.write('Tiempo en creacion medicion whatsapp: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    whatsapp = True
                elif result['test_name'] == 'vanilla_tor' and not vanilla_tor:
                    f.write('Tiempo en creacion medicion vanilla_tor: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    vanilla_tor = True
                elif result['test_name'] == 'facebook_messenger' and not facebook_messenger:
                    f.write('Tiempo en creacion medicion facebook_messenger: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    facebook_messenger = True
                elif result['test_name'] == 'ndt' and not ndt:
                    f.write('Tiempo en creacion medicion ndt: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    ndt = True
                elif result['test_name'] == 'dash' and not dash:
                    f.write('Tiempo en creacion medicion dash: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    dash = True
                elif result['test_name'] == 'telegram' and not telegram:
                    f.write('Tiempo en creacion medicion telegram: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    telegram = True
                elif result['test_name'] == 'psiphon' and not psiphon:
                    f.write('Tiempo en creacion medicion psiphon: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    psiphon = True
                elif result['test_name'] == 'sni_blocking' and not sni_blocking:
                    f.write('Tiempo en creacion medicion sni_blocking: ')
                    f.write(str(meas_cr_fin-meas_cr_ini))
                    f.write('\n')
                    sni_blocking = True
                
                # fp.report_ready = True
                # data_state = FastPath.DataReady.READY
                start_time_datetime = datetime.datetime.strptime(ms.measurement_start_time, "%Y-%m-%d %H:%M:%S") # convert date into string
                print(c.green(f"Trying to update cache, start time: {ms.measurement_start_time}, cache: {cache_min_date}. Is less: {start_time_datetime < cache_min_date}"))
                if start_time_datetime < cache_min_date:
                    cache_min_date = start_time_datetime
                    print(c.red("Updating min date cache:"), c.cyan(cache_min_date))

            except:
                pass
                # fp.report_ready = False
                # data_state = FastPath.DataReady.UNDETERMINED

            # fp.data_ready = data_state
            # fp.save()
            # saved_measurements.append(fp.id)

            # if limit and (len(saved_measurements) >= limit):
            #     break

    day_time_end=time.time()
    f.write('Tiempo en un dia de ingesta: ')
    f.write(str(day_time_end-day_time_ini))
    f.write('\n')   
    f.close()

    return (status_code)


def update_measurement_table(
                            n_measurements : int = None,
                            test_name      : str = None,
                            retrys         : int = -1
                            ) -> dict:
    """
        Store at the most 'n_measurements' ready measurements of type 'test_name'
        into the  database. Defaults to all measurements yo can add, for
        any kind of measurement.

        Set the measurements with a 'try' value greater than 'retrys' as DEAD.
        If 'retrys' is negative, then it is never set to DEAD, no matter how many trys it has.

        This function will update the Measurement table
        and the fast path table depending on the availability of
        measurements in the fast path table.

        Get every measurement in the database whose report_ready
        is set to false or None, and whose catch_date - now > 24h.
        perform a request for the measurementl.
        If the measurement is available, change report_ready to true and
        create a new measurement object in the database. Otherwise,
        report_ready is set to null.

        Returns a dict with two fields:
            success: Ammount of new measurements succesfully saved
            error:   Ammount of undetermined measurements
    """
    # from apps.api.fp_tables_api.utils import update_measurement_table

    treshold = timezone.now() - timezone.timedelta(days=1)
    # Get interesting measurements:
    fpMeasurements =    FastPath.objects\
                                .exclude(data_ready=FastPath.DataReady.READY)\
                                .exclude(data_ready=FastPath.DataReady.DEAD)\
                                .filter(catch_date__lt=treshold)

    # Filter by test_name
    if test_name:
        fpMeasurements = fpMeasurements.filter(test_name=test_name)

    # Limit to n_measurements
    if n_measurements:
        fpMeasurements = fpMeasurements[:n_measurements]

    measurements_url = "https://api.ooni.io/api/v1/measurements"

    # Save the measurements at the end
    # in case something fails
    meas_to_save = []       # Measurements with errors
    new_measurements = []   # New Measurements with their fp equivalent
    for fp in fpMeasurements:

        # Ask for the measurement based on its report id

        try:
            req = requests.get(
                measurements_url,
                params={
                    "report_id" : fp.report_id,
                    "input" : fp.input,
                    'test_name' : fp.test_name,
                    "limit":5000,
                })
        except:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Unvalid GET request")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        # If the measurement could not be found, search for it later
        if req.status_code != 200:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Report not found")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        data = req.json()
        data = data.get("results")

        if data == None:
            raise AttributeError("Unexpected data format from Ooni")

        measurement = [d for d in data if 
                        dateparse.parse_datetime(d.get("measurement_start_time")) == fp.measurement_start_time or
                        dateparse.parse_datetime(d.get("measurement_start_time")) == (fp.measurement_start_time + datetime.timedelta(days=4)) # PQC
                        ]

        print("data: ", data) 

        if len(measurement) != 1:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Too many equal measurements: ", len(measurement))
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        # Get the measurement data
        measurement = measurement[0]

        # Update the url if it has changed
        new_url = measurement.get("measurement_url")
        if new_url != fp.measurement_url and new_url != None:
            fp.measurement_url = new_url

        # Request data for the Measurement Table
        try:
            req = requests.get(fp.measurement_url)
        except:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("invalid GET request fetching measurement data")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        # If data could not be found or a network error ocurred,
        # mark this as incomplete and process the following measurements
        if req.status_code != 200:
            print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Could not fetch measurement data")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        data = req.json()

        # Update the id if it has changed
        new_id = data.get("id")
        if new_id != fp.tid and new_id != None:
            fp.tid = new_id

        # If there's no id, then we have some unconsistent data. UPDATE: or not, because now is not provided
        # if new_id == None:
        #     print("Could not find measurement: ", fp.input, ", ", fp.measurement_start_time)
        #     print("Measurement does not provides any id")
        #     fp.report_ready = None
        #     meas_to_save.append(fp)
        #     continue    

        new_measurement = RawMeasurement(
            input=data['input'],
            report_id= data['report_id'],
            report_filename= data.get('report_filename','NO_AVAILABLE'), #
            options= data.get('options', "NO_AVAILABLE"), #
            probe_cc= data.get('probe_cc','VE'),
            probe_asn= data['probe_asn'],
            probe_ip=data.get('probe_ip'),
            data_format_version= data['data_format_version'],
            test_name= data['test_name'],
            test_start_time= data.get('test_start_time'),
            measurement_start_time= data['measurement_start_time'],
            test_runtime= data.get('test_runtime'),
            test_helpers= data.get('test_helpers',"NO_AVAILABLE"),
            software_name= data['software_name'],
            software_version= data['software_version'],
            test_version= data['test_version'],
            bucket_date= data.get('bucket_date'), #
            test_keys= data['test_keys'],
            annotations= data['annotations']
        )
        
        fp.report_ready = True
        new_measurements.append((new_measurement, fp))
        #new_measurements.append(new_measurement)
        #meas_to_save.append(fp)

    results = {
        "success" : 0, # ammount of succesfully saved new measurements
        "error"   : 0, # ammount of undetermined measurements
    }
    for fp in meas_to_save:
        results["error"] += 1
        if retrys >= 0 and fp.trys > retrys:
            fp.data_ready = FastPath.DataReady.DEAD
        else:
            fp.data_ready = FastPath.DataReady.UNDETERMINED
            fp.trys += 1

        fp.save()

    for (meas, fp) in new_measurements:
        try:
            meas.save()
            fp.data_ready = FastPath.DataReady.READY
            results["success"] += 1

        except Exception as e:
            print("Could not save measurement: ", fp.input, ", ", fp.measurement_start_time)
            print("Could not save measurement: ", meas.input, ", ", meas.measurement_start_time)
            print("Error", e)
            fp.report_ready = None
            # set this measurement as undetermined and increse its number of trys
            fp.data_ready = FastPath.DataReady.UNDETERMINED
            fp.trys += 1

            results["error"] += 1

        try:
            fp.save()
        except:
            pass

    return results