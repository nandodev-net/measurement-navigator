
# Django imports
from django.test import TestCase

# Local imports

from .utils                         import *
from .models                        import *
from apps.main.measurements.models  import Measurement, RawMeasurement

# Create your tests here.

class TestCreateSubMeasurement(TestCase):
    """
        Test suite to test functions related to creation of 
        DNS submeasurements from raw measurements
    """

    def setUp(self):

        # I suggest you to keep this not collapsed in your IDE unless you 
        # want to inspect the data
        test_keys = {
            "accessible": True,
            "agent": "redirect",
            "blocking": False,
            "body_length_match": None,
            "body_proportion": 0,
            "client_resolver": "201.249.172.72",
            "control": {
            "dns": {
                "addrs": [
                "173.236.245.145"
                ],
                "failure": None
            },
            "http_request": {
                "body_length": -1,
                "failure": "unknown_error",
                "headers": {},
                "status_code": -1
            },
            "tcp_connect": {
                "173.236.245.145:443": {
                "failure": None,
                "status": True
                }
            }
            },
            "control_failure": None,
            "dns_consistency": "consistent",
            "dns_experiment_failure": None,
            "headers_match": None,
            "http_experiment_failure": "ssl_error: error:14007086:SSL routines:CONNECT_CR_CERT:certificate verify failed",
            "queries": [
            {
                "answers": [
                {
                    "answer_type": "CNAME",
                    "hostname": "fsrn.org",
                    "ttl": None
                },
                {
                    "answer_type": "A",
                    "ipv4": "173.236.245.145",
                    "ttl": None
                }
                ],
                "engine": "system",
                "failure": None,
                "hostname": "fsrn.org",
                "query_type": "A",
                "resolver_hostname": None,
                "resolver_port": None
            }
            ],
            "requests": [
            {
                "failure": "ssl_error: error:14007086:SSL routines:CONNECT_CR_CERT:certificate verify failed",
                "request": {
                "body": "",
                "headers": {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US;q=0.8,en;q=0.5",
                    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36"
                },
                "method": "GET",
                "tor": {
                    "exit_ip": None,
                    "exit_name": None,
                    "is_tor": False
                },
                "url": "https://fsrn.org/"
                },
                "response": {
                "body": None,
                "headers": {}
                }
            }
            ],
            "retries": None,
            "socksproxy": None,
            "status_code_match": None,
            "tcp_connect": [
            {
                "ip": "173.236.245.145",
                "port": 443,
                "status": {
                "blocked": False,
                "failure": None,
                "success": True
                }
            }
            ],
            "title_match": None
        }
        meas = RawMeasurement(
            id= "6333ce81-143b-47fe-a605-ec16de9fc847",
            input= "https://fsrn.org/",
            report_id="20200930T110836Z_AS8048_iJjN525JD47lLWpP2vheZ5mBWefWsq2j1zxsR0aqcYHukMKa5c",
            report_filename="filename",
            options= [],
            probe_asn="AS8048",
            probe_cc= "VE",
            probe_ip="127.0.0.1",
            data_format_version="0.2.0",
            test_name= "web_connectivity",
            test_start_time= "2020-09-30 11:08:34",
            measurement_start_time= "2020-09-30 11:08:49",
            test_runtime=4.1357738972,
            test_helpers={},
            software_name= "web_con_test1",
            software_version= "1.0",
            test_version="1.0",
            bucket_date= "2020-09-30 11:08:34",
            test_keys= test_keys,
            annotations={}
        )
        meas.save()

        # I suggest you to keep this not collapsed in your IDE unless you 
        # want to inspect the data
        test_keys = {
            "control": {
                "tcp_connect": {
                "198.71.49.226:443": {
                    "status": True,
                    "failure": None
                }
                },
                "http_request": {
                "body_length": 62077,
                "failure": None,
                "title": "Veneloga",
                "headers": {
                    "X-Cache-Status": "HIT",
                    "Expires": "Fri, 02 Oct 2020 14:13:51 GMT",
                    "Date": "Thu, 01 Oct 2020 14:14:05 GMT",
                    "X-Powered-By": "PleskLin",
                    "Strict-Transport-Security": "max-age=15768000; includeSubDomains",
                    "Vary": "Accept-Encoding",
                    "Server": "nginx",
                    "X-Lost": "...In Translation",
                    "ETag": "W/\"Thu, 01 Oct 2020 14:11:29 GMT\"",
                    "Pragma": "",
                    "Cache-Control": "max-age=0, s-maxage=62055, must-revalidate",
                    "Last-Modified": "Thu, 01 Oct 2020 14:11:29 GMT",
                    "X-Frame-Options": "SAMEORIGIN",
                    "Content-Type": "text/html; charset=ISO-8859-15"
                },
                "status_code": 200
                },
                "dns": {
                "failure": None,
                "addrs": [
                    "venelogia.com",
                    "198.71.49.226"
                ]
                }
            },
            "retries": None,
            "control_failure": None,
            "socksproxy": None,
            "http_experiment_failure": None,
            "agent": "redirect",
            "headers_match": True,
            "client_resolver": "172.253.242.107",
            "tcp_connect": [
                {
                "status": {
                    "failure": None,
                    "success": True,
                    "blocked": False
                },
                "ip": "198.71.49.226",
                "port": 443,
                "t": 1.317684218
                }
            ],
            "dns_consistency": "consistent",
            "dns_experiment_failure": None,
            "body_proportion": 1,
            "blocking": False,
            "queries": [
                {
                "engine": "system",
                "resolver_hostname": None,
                "query_type": "A",
                "hostname": "www.venelogia.com",
                "answers": [
                    {
                    "as_org_name": "1&1 IONOS SE",
                    "ipv4": "198.71.49.226",
                    "asn": 8560,
                    "answer_type": "A",
                    "ttl": None
                    }
                ],
                "failure": None,
                "t": 0.09348276,
                "resolver_address": "",
                "resolver_port": None
                }
            ],
            "body_length_match": True,
            "requests": [
                {
                "failure": None,
                "request": {
                    "body": "",
                    "headers": {
                    "Host": "www.venelogia.com",
                    "Accept-Language": "en-US;q=0.8,en;q=0.5",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
                    },
                    "tor": {
                    "is_tor": False,
                    "exit_ip": None,
                    "exit_name": None
                    },
                    "headers_list": [
                    [
                        "Accept",
                        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                    ],
                    [
                        "Accept-Language",
                        "en-US;q=0.8,en;q=0.5"
                    ],
                    [
                        "Host",
                        "www.venelogia.com"
                    ],
                    [
                        "User-Agent",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
                    ]
                    ],
                    "url": "https://www.venelogia.com/",
                    "body_is_truncated": False,
                    "method": "GET"
                },
                "response": {
                    "body": {
                    "data":"deleted for brevity",
                    "format": "base64"
                    },
                    "headers_list": [
                    [
                        "Cache-Control",
                        "max-age=0, s-maxage=62055, must-revalidate"
                    ],
                    [
                        "Content-Type",
                        "text/html; charset=ISO-8859-15"
                    ],
                    [
                        "Date",
                        "Thu, 01 Oct 2020 14:14:08 GMT"
                    ],
                    [
                        "Etag",
                        "\"Thu, 01 Oct 2020 14:11:29 GMT\""
                    ],
                    [
                        "Expires",
                        "Fri, 02 Oct 2020 14:13:51 GMT"
                    ],
                    [
                        "Last-Modified",
                        "Thu, 01 Oct 2020 14:11:29 GMT"
                    ],
                    [
                        "Pragma",
                        ""
                    ],
                    [
                        "Server",
                        "nginx"
                    ],
                    [
                        "Strict-Transport-Security",
                        "max-age=15768000; includeSubDomains"
                    ],
                    [
                        "Vary",
                        "Accept-Encoding"
                    ],
                    [
                        "X-Cache-Status",
                        "HIT"
                    ],
                    [
                        "X-Frame-Options",
                        "SAMEORIGIN"
                    ],
                    [
                        "X-Lost",
                        "...In Translation"
                    ],
                    [
                        "X-Powered-By",
                        "PleskLin"
                    ]
                    ],
                    "code": 200,
                    "body_is_truncated": False,
                    "headers": {
                    "X-Cache-Status": "HIT",
                    "Expires": "Fri, 02 Oct 2020 14:13:51 GMT",
                    "Date": "Thu, 01 Oct 2020 14:14:08 GMT",
                    "X-Powered-By": "PleskLin",
                    "Strict-Transport-Security": "max-age=15768000; includeSubDomains",
                    "Vary": "Accept-Encoding",
                    "Server": "nginx",
                    "X-Lost": "...In Translation",
                    "Etag": "\"Thu, 01 Oct 2020 14:11:29 GMT\"",
                    "Pragma": "",
                    "Cache-Control": "max-age=0, s-maxage=62055, must-revalidate",
                    "Last-Modified": "Thu, 01 Oct 2020 14:11:29 GMT",
                    "X-Frame-Options": "SAMEORIGIN",
                    "Content-Type": "text/html; charset=ISO-8859-15"
                    }
                },
                "t": 0.000826875
                }
            ],
            "accessible": True,
            "title_match": False,
            "x_status": 1,
            "status_code_match": True
            }
        
        meas = RawMeasurement(
            id= "dfe85c88-c1ea-843b-2cfe-8f3b55016886",
            input= "https://www.venelogia.com/",
            report_id="20200930T110836Z_AS8048_iJjN525JD47lLWpP2vheZ5mBWefWsq2j1zxsR0aqcYHukMKa5c",
            report_filename="filename",
            options= [],
            probe_asn="AS8048",
            probe_cc= "VE",
            probe_ip="127.0.0.1",
            data_format_version="0.2.0",
            test_name= "web_connectivity",
            test_start_time= "2020-09-30 11:08:34",
            measurement_start_time= "2020-09-30 11:08:49",
            test_runtime=4.1357738972,
            test_helpers={},
            software_name= "web_con_test1",
            software_version= "1.0",
            test_version="1.0",
            bucket_date= "2020-09-30 11:08:34",
            test_keys= test_keys,
            annotations={}
        )
        meas.save()

    def testDNSCreateFromWebConn(self):
        """
            Test the creation of a DNS submeasurement given a valid
            web_connectivity measurement
        """

        rmeas = RawMeasurement.objects.get(id="6333ce81-143b-47fe-a605-ec16de9fc847")
        obtainedAns = createDNSFromWebConn(rmeas)
        desiredAns = DNS(
            measurement=None,
            flag=None,
            control_resolver_failure=None,
            control_resolver_answers={"addrs":["173.236.245.145"]},
            failure=None,
            answers=[
                {
                    "answer_type": "CNAME",
                    "hostname": "fsrn.org",
                    "ttl": None
                },
                {
                    "answer_type": "A",
                    "ipv4": "173.236.245.145",
                    "ttl": None
                }
                ],
            hostname="fsrn.org",
            dns_consistency="consistent",
            inconsistent=False
        )
        # Check that every field is the same except for the  _state django field (first field)
        assert(len(obtainedAns) == 1 and 
                list(vars(desiredAns).items())[1:] == list(vars(obtainedAns[0]).items())[1:])
        

    def testCreateDNSFromDNSCons(self):
        """
            Test the creation of a DNS submeasurement based on a 
            DNS Test.
            @FROZEN necesito una medicion de tipo dns_consistency para poder probar
        """
        pass

    def testCreateHTTPFromWebConNone(self):
        """
            Test the creation of a HTTP submeasurement based on a valid 
            web_connectivity measurement where the connection was lost.
            In fact, there should not be a submeasurement since this measurement is
            meaningless due to the lack of information. 'None' is expected as
            output result
        """
        rmeas = RawMeasurement.objects.get(id="6333ce81-143b-47fe-a605-ec16de9fc847")

        obtainedAns = createHTTPFromWebCon(rmeas)

        assert(None == obtainedAns)

    def testCreateHTTPFromWebCon(self):
        """
            Test the creation of a HTPP submeasurement based on a valid web_connectivity
            measurement where the connection is stable.
        """
        rmeas = RawMeasurement.objects.get(id="dfe85c88-c1ea-843b-2cfe-8f3b55016886")

        obtainedAns = createHTTPFromWebCon(rmeas)
        desiredAns = HTTP(
            measurement=None,
            flag=None, 
            status_code_match=True,
            headers_match=True,
            body_length_match=True,
            body_proportion=1
        )

        assert(list(vars(desiredAns).items())[1:] == list(vars(obtainedAns).items())[1:])

    def testCreateTCPFromWebCon(self):
        rmeas = RawMeasurement.objects.get(id="dfe85c88-c1ea-843b-2cfe-8f3b55016886")

        obtainedAns = createTCPFromWebCon(rmeas)
        desiredAns = [
                TCP(
                    measurement=None, 
                    flag=None, 
                    status_blocked=False, 
                    status_success=True, 
                    status_failure=None, 
                    ip="198.71.49.226" )
            ]

        assert(len(obtainedAns) == 1 and 
                list(vars(desiredAns[0]).items())[1:] == list(vars(obtainedAns[0]).items())[1:])