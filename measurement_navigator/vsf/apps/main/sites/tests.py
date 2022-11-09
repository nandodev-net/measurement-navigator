
# Django imports
from django.test import TestCase

# Third party imports
import json
import datetime

# Local imports
from .utils                             import *
from .models                            import *
from apps.main.ooni_fp.fp_tables.models import FastPath
from apps.main.measurements.models      import Measurement

class URLUpdateReferences(TestCase):
    """
        Test class for checking functionality of
        URL Updating functions
    """

    def setUp(self):
        URL.objects.create(url="http://www.vesinfiltro.com", site=None)
        URL.objects.create(url="http://www.why2.com", site=None)
        URL.objects.create(url="http://www.why3.com", site=None)

        FastPath.objects.create(
            anomaly=True,
            confirmed=False,
            failure=False,
            input = "http://www.why2.com",
            tid="temp-fid-00b89c9a09c892158ca441b370c718b8",
            measurement_start_time= datetime.date.today(),
            measurement_url="www.ooni.com/path/to/report",
            probe_asn="CANTV",
            probe_cc="VE",
            report_id="123report123",
            test_name="web_connectivity",
            catch_date=datetime.date.today(),
            scores = {}
        )
        FastPath.objects.create(
            anomaly=True,
            confirmed=False,
            failure=False,
            input = "http://www.why3.com",
            tid="temp-fid-00b89c9a09c892158ca441b370c718b9",
            measurement_start_time= datetime.date.today(),
            measurement_url="www.ooni.com/path/to/report",
            probe_asn="CANTV",
            probe_cc="VE",
            report_id="123report123",
            test_name="web_connectivity",
            catch_date=datetime.date.today(),
            scores = {}
        )
        FastPath.objects.create(
            anomaly=True,
            confirmed=False,
            failure=False,
            input = "http://www.why3.com",
            tid="temp-fid-00b89c9a09c892158ca441b370c718b7",
            measurement_start_time= datetime.date.today(),
            measurement_url="www.ooni.com/path/to/report",
            probe_asn="CANTV",
            probe_cc="VE",
            report_id="123report123",
            test_name="web_connectivity",
            catch_date=datetime.date.today(),
            scores = {}
        )
        Measurement.objects.create(
            bucket_date=datetime.date.today(),
            input="http://www.why3.com",
            report_id="someid",
            report_filename="somefile.json",
            probe_cc="VE",
            probe_asn="CANTV",
            probe_ip="1.1.1.1",
            data_format_version="0.2.0",
            test_name="web_connectivity",
            test_start_time=datetime.date.today(),
            measurement_start_time=datetime.date.today(),
            test_runtime=0.1,
            software_name="ooni",
            software_version="420",
            test_version="69",
            test_keys={},
            id='00b89c9a09c892158ca441b370c718b9',
            annotations={}
        )

        Measurement.objects.create(
            bucket_date=datetime.date.today(),
            input="http://www.why3.com",
            report_id="someid",
            report_filename="somefile.json",
            probe_cc="VE",
            probe_asn="CANTV",
            probe_ip="1.1.1.1",
            data_format_version="0.2.0",
            test_name="web_connectivity",
            test_start_time=datetime.date.today(),
            measurement_start_time=datetime.date.today(),
            test_runtime=0.1,
            software_name="ooni",
            software_version="420",
            test_version="69",
            test_keys={},
            id='00b89c9a09c892158ca441b370c718b7',
            annotations={}
        )

        Measurement.objects.create(
            bucket_date=datetime.date.today(),
            input="http://www.why2.com",
            report_id="someid",
            report_filename="somefile.json",
            probe_cc="VE",
            probe_asn="CANTV",
            probe_ip="1.1.1.1",
            data_format_version="0.2.0",
            test_name="web_connectivity",
            test_start_time=datetime.date.today(),
            measurement_start_time=datetime.date.today(),
            test_runtime=0.1,
            software_name="ooni",
            software_version="420",
            test_version="69",
            test_keys={},
            id='00b89c9a09c892158ca441b370c718b8',
            annotations={}
        )

    def testUpdateReferences(self):
        """
            This test is intended to check if update_urls_fp_refs() it's working
            properly with the usual input. Why2 should have 1 references, why3 should have
            2 references, and vesinfiltro should remain empty since it has no fast path
            measurements
        """

        update_urls_fp_refs()
        why3 = URL.objects.get(url="http://www.why3.com").fp_references
        why3_result = ["temp-fid-00b89c9a09c892158ca441b370c718b7", "temp-fid-00b89c9a09c892158ca441b370c718b9"]
        why2 = URL.objects.get(url="http://www.why2.com").fp_references
        why2_result = ["temp-fid-00b89c9a09c892158ca441b370c718b8"]
        vsf  = URL.objects.get(url="http://www.vesinfiltro.com").fp_references

        assert  ( all( [url in why3_result for url in why3["references"]] ) )
        assert  ( all( [url in why2_result for url in why2["references"]] ) )
        assert  ( vsf == {} )

    def testNoDuplicatedReferences(self):
        """
            This test is intended to check whether a reference to a measurement is
            being added exactly once
        """
        update_urls_fp_refs() # Now the reference has been added once
        update_urls_fp_refs() # Idempotency should ensure that multiple calls
                              # doesn not add duplicated data
        why2 = URL.objects.get(url="http://www.why2.com").fp_references
        why2_result = ["temp-fid-00b89c9a09c892158ca441b370c718b8"]

        assert  ( all( [url in why2_result for url in why2["references"]] ) and len(why2) == 1)

    def testUpdateReports(self):
        """
            This test is intended to check if update_urls_reports() it's working
            properly with the usual input. Why2 should have 1 references, why3 should have
            2 references, and vesinfiltro should remain empty since it has no fast path
            measurements
        """

        update_urls_reports()
        why3 = URL.objects.get(url="http://www.why3.com").reports
        why3_result = ["00b89c9a09c892158ca441b370c718b7", "00b89c9a09c892158ca441b370c718b9"]
        why2 = URL.objects.get(url="http://www.why2.com").reports
        why2_result = ["00b89c9a09c892158ca441b370c718b8"]
        vsf  = URL.objects.get(url="http://www.vesinfiltro.com").reports

        assert  ( all( [url in why3_result for url in why3["reports"]] ) )
        assert  ( all( [url in why2_result for url in why2["reports"]] ) )
        assert  ( vsf == {} )

    def testNoDuplicatedReports(self):
        """
            This test is intended to check whether a reference to a report is
            being added exactly once
        """
        update_urls_reports() # Now the reference has been added once
        update_urls_reports() # Idempotency should ensure that multiple calls
                              # doesn't not add duplicated data
        why2 = URL.objects.get(url="http://www.why2.com").reports
        why2_result = ["00b89c9a09c892158ca441b370c718b8"]

        assert  ( all( [url in why2_result for url in why2["reports"]] ) and len(why2) == 1)
