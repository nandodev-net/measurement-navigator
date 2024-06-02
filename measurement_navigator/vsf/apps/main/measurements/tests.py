from django.test import TestCase

from .utils import *


class SoftFlagCheckTest(TestCase):
    """
    Test class for checking functionality of
    soft flags checking functions
    """

    def setUp(self):
        """
        # Get a well-known measurement measurement. This is a web connectivity measurement
        req = requests.get('https://api.ooni.io/api/v1/measurement/temp-id-432863629')
        if req.status_code >= 300:
            raise LookupError("Could not get test data samples from ooni")

        req = req.json()

        # we use the software name as a control variable since it is not relevant
        # for this kind of tests
        meas = Measurement(
            id=req["id"],
            input= req["input"],
            report_filename=req["report_filename"],
            options=req["options"],
            probe_asn=req["probe_asn"],
            probe_cc= req["probe_cc"],
            probe_ip=req["probe_ip"],
            data_format_version=req["data_format_version"],
            test_name= req["test_name"],
            test_start_time= req["test_start_time"],
            measurement_start_time= req["measurement_start_time"],
            test_runtime=req["test_runtime"],
            test_helpers=req["test_helpers"],
            software_name= "web_con_test1",
            software_version= req["software_version"],
            test_version=req["test_version"],
            bucket_date= req["bucket_date"],
            flag = None,
            test_keys= req["test_keys"],
            annotations= req["annotations"]
        )
        meas.save()
        """
        pass

    def testDnsTestingOk(self):
        """
        Normal test: given a non anomaly "measurement", return False
        """
        control = {"addrs": ["1.1.1.1", "2.2.2.2", "3.3.3.3"], "failure": None}
        test_keys = {
            "queries": [
                {
                    "answers": [
                        {"answer_type": "A", "ipv4": "1.1.1.1"},
                        {"answer_type": "A", "ipv4": "2.2.2.2"},
                        {"answer_type": "CNAME", "hostname": "You may ignore me"},
                    ],
                    "answers": [
                        {"answer_type": "A", "ipv4": "1.1.1.1"},
                        {"answer_type": "A", "ipv4": "3.3.3.3"},
                    ],
                }
            ]
        }

        assert not check_dns_test(test_keys, control)

    def testDnsTestingAnomaly(self):
        """
        Normal test: given an anomaly "measurement", return True
        """
        control = {"addrs": ["1.1.1.1", "2.2.2.2", "3.3.3.3"], "failure": None}
        test_keys = {
            "queries": [
                {
                    "answers": [
                        {"answer_type": "A", "ipv4": "1.1.1.1"},
                        {"answer_type": "A", "ipv4": "2.2.2.2"},
                        {"answer_type": "CNAME", "hostname": "You may ignore me"},
                    ],
                    "answers": [
                        {"answer_type": "A", "ipv4": "1.1.1.1"},
                        {"answer_type": "A", "ipv4": "4.3.3.3"},
                    ],
                }
            ]
        }

        assert check_dns_test(test_keys, control)

    def testDnsTestingOkEmpty(self):
        """
        Normal test: given a non anomaly "measurement" with emmpty queries, return False
        """
        control = {"addrs": ["1.1.1.1", "2.2.2.2", "3.3.3.4"], "failure": None}
        test_keys = {"queries": []}

        assert not check_dns_test(test_keys, control)

    def testDnsTestingOkFailure(self):
        """
        Check that the check returns false when the control
        measurement failed
        """
        control = {"addrs": None, "failure": "I failed"}
        test_keys = {"queries": []}
        assert not check_dns_test(test_keys, control)
