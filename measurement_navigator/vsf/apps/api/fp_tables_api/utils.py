"""
    Additional functionality to perform validations in the post request
"""

import collections
import datetime
import linecache
import os
# Python imports
import tracemalloc
from typing import List, Optional, Tuple
from urllib.parse import urlencode

import django.utils.dateparse as dateparse
import django.utils.timezone as timezone
# Third party imports
import requests
from django.core.paginator import Paginator

from apps.main.measurements.models import RawMeasurement
from apps.main.measurements.post_save_utils import (
    post_save_rawmeasurement, post_save_rawmeasurement_list)
from apps.main.ooni_fp.fp_tables.models import FastPath
# Local imports
from apps.main.sites.models import URL
# Bulk create manager import
from vsf.bulk_create_manager import BulkCreateManager


def check_post_data(data) -> bool:
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
        raise TypeError(
            "Data parameter in checkPostData should be a Mapping type object"
        )

    since = data.get("since")
    until = data.get("until")
    probe_cc = data.get("probe_cc")

    # Check if every field is a string
    if (
        (not isinstance(since, str))
        or (not isinstance(until, str))
        or (not isinstance(probe_cc, str))
    ):
        print("bad types")
        return False

    # Check valid fields
    if (since == None) or (until == None) or (probe_cc == None):
        return False

    date_format = "%Y-%m-%d"
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


def request_fp_data(
    since: str,
    until: str,
    test_name: Optional[str] = None,
    probe_asn: Optional[str] = None,
    anomaly: Optional[str] = None,
    from_fastpath: bool = True,
    limit: Optional[int] = None,
) -> Tuple[int, List[str]]:
    """
        Given the start and end date for a set of measurements,
        perform a get request to ooni in order to get the
        recent fast path objects and store them in the database.

    Args:
        since (str): Start date for when to ask for measurements. Expected in format: YYYY-mm-dd.
        until (str): Final date for when to ask for measurements. Expected in format: YYYY-mm-dd.
        test_name (Optional[str], optional): Name of test whose data you want to pull, all tests if not specified. Defaults to None.
        probe_asn (Optional[str], optional): ASN whose data you want to pull, all ASNs if not specified. Defaults to None.
        anomaly (Optional[str], optional): Anomaly value for this measurements, any value if not specified. Defaults to None.
        from_fastpath (bool, optional): [LEGACY] if measurements should come from the fastpath. Defaults to True.
        limit (Optional[int], optional): How many measurements to pull, as much as possible if not provided. Defaults to None.

    Returns:
        Tuple[int, List[str]]: (Status code for request, List of ids of actually added measurements)
    """

    from vsf.utils import Colors as c

    page_req = False

    # Data validation
    data = {
        "probe_cc": "VE",  # In case we want to add other countries
        "since": since,
        "until": until,
        "order": "asc",
        "order_by": "measurement_start_time",
        "probe_asn": probe_asn,
        "anomaly": anomaly,
    }

    if limit is not None and limit > 0:
        data["limit"] = limit

    if test_name:
        data["test_name"] = test_name

    # Check if the post data is valid:
    if not check_post_data(data):
        raise AttributeError(
            "Unvalid input arguments. Given: \n"
            + "   Since: "
            + since
            + "\n"
            + "   Until: "
            + until
        )

    # Perform a get request from Ooni
    next_url = "https://api.ooni.io/api/v1/measurements?" + urlencode(data)

    status_code = 200
    new_ms_to_report = []
    while next_url != None:
        try:
            # If it wasn't able to get the next page data, just store the currently added data
            # @TODO we have to think what to do in this cases

            print(c.magenta("\n\nRequesting URL: \n"), next_url)
            req = requests.get(next_url)
            new_meas_list = []

            if not page_req:
                page_req = True

            status_code = req.status_code
            assert req.status_code == 200
        except:
            break

        # Since everything went ok, we get the data in json format
        data = req.json()
        metadata = data["metadata"]
        next_url = metadata.get("next_url")
        if from_fastpath:
            results = filter(
                # since we just care about fast path data, we filter the ones whose measurement_id begins with
                # 'temp-fid' according to what Federico (from ooni) told us
                # UPDATE: by today, measurement_id is not reported by the ooni queries, so
                # we can't rely on it to check whether a measurement comes from the fastpath or not.
                # @TODO
                lambda res: res.get("measurement_id", "").startswith("temp-fid"),
                data["results"],
            )
        else:
            results = data["results"]

        # to TOR measurements we create an 'tor' url, because TOR is not a webpage it is a service.
        for result in results:
            URL.objects.get_or_create(url=str(result["input"]))
            if result["test_name"] == "tor":
                URL.objects.get_or_create(url="tor")
            try:
                req = requests.get(result["measurement_url"])
                status_code = req.status_code
                assert req.status_code == 200
            except:
                continue

            # checking if the Raw meas exists, if not we create it.
            raw_object = RawMeasurement.objects.filter(
                input=result["input"],
                report_id=result["report_id"],
                probe_asn=result["probe_asn"],
                test_name=result["test_name"],
                measurement_start_time=result["measurement_start_time"],
            )
            if len(raw_object) == 0:
                data = req.json()
                if data["test_name"] == "tor":
                    input_ = "tor"
                else:
                    input_ = data["input"]
                ms = RawMeasurement(
                    input=input_,
                    report_id=data["report_id"],
                    report_filename=data.get("report_filename", "NO_AVAILABLE"),  #
                    options=data.get("options", "NO_AVAILABLE"),  #
                    probe_cc=data.get("probe_cc", "VE"),
                    probe_asn=data["probe_asn"],
                    probe_ip=data.get("probe_ip"),
                    data_format_version=data["data_format_version"],
                    test_name=data["test_name"],
                    test_start_time=data.get("test_start_time"),
                    measurement_start_time=data["measurement_start_time"],
                    test_runtime=data.get("test_runtime"),
                    test_helpers=data.get("test_helpers", "NO_AVAILABLE"),
                    software_name=data["software_name"],
                    software_version=data["software_version"],
                    test_version=data["test_version"],
                    bucket_date=data.get("bucket_date"),  #
                    test_keys=data["test_keys"],
                    annotations=data["annotations"],
                    is_processed=False,
                )

                # Eliminando body de las web_connectivity
                if ms.test_name == "web_connectivity":
                    if not ms.test_keys or not ms.test_keys.get("requests"):
                        pass
                    else:
                        for r in ms.test_keys["requests"]:
                            if r["response"].get("body"):
                                del r["response"]["body"]
                                r["response"]["body"] = "Not_available"

                new_meas_list.append(ms)
                print("current new measuremnt list size: ", len(new_meas_list))

        try:
            print(c.magenta("Creating a new measurement"))

            # Agregando data por lotes de 200
            bulk_mgr = BulkCreateManager(chunk_size=500)
            for ms_ in new_meas_list:
                bulk_mgr.add(ms_)
                new_ms_to_report.append(ms_.id)
            bulk_mgr.done()
        except:
            pass

    paginator = Paginator(
        RawMeasurement.objects.filter(is_processed=False).order_by("test_start_time"),
        500,
    )
    for page in range(1, paginator.num_pages + 1):
        raw_list_to_process = paginator.page(page).object_list
        for raw in raw_list_to_process:
            post_save_rawmeasurement(raw)

    return (status_code, new_ms_to_report)


def update_measurement_table(
    n_measurements: Optional[int] = None,
    test_name: Optional[str] = None,
    retrys: int = -1,
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
    fp_measurements = (
        FastPath.objects.exclude(data_ready=FastPath.DataReady.READY)
        .exclude(data_ready=FastPath.DataReady.DEAD)
        .filter(catch_date__lt=treshold)
    )

    if fp_measurements.count() == 0:
        return {"sucess": 0, "error": 0}

    # Filter by test_name
    if test_name:
        fp_measurements = fp_measurements.filter(test_name=test_name)

    # Limit to n_measurements
    if n_measurements:
        fp_measurements = fp_measurements[:n_measurements]

    measurements_url = "https://api.ooni.io/api/v1/measurements"

    # Save the measurements at the end
    # in case something fails
    meas_to_save = []  # Measurements with errors
    new_measurements = []  # New Measurements with their fp equivalent
    for fp in fp_measurements:

        # Ask for the measurement based on its report id

        try:
            req = requests.get(
                measurements_url,
                params={
                    "report_id": fp.report_id,
                    "input": fp.input,
                    "test_name": fp.test_name,
                    "limit": 5000,
                },
            )
        except:
            print(
                "Could not find measurement: ",
                fp.input,
                ", ",
                fp.measurement_start_time,
            )
            print("Unvalid GET request")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        # If the measurement could not be found, search for it later
        if req.status_code != 200:
            print(
                "Could not find measurement: ",
                fp.input,
                ", ",
                fp.measurement_start_time,
            )
            print("Report not found")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        data = req.json()
        data = data.get("results")

        if data == None:
            raise AttributeError("Unexpected data format from Ooni")

        measurement = [
            d
            for d in data
            if dateparse.parse_datetime(d.get("measurement_start_time"))
            == fp.measurement_start_time
            or dateparse.parse_datetime(d.get("measurement_start_time"))
            == (fp.measurement_start_time + datetime.timedelta(days=4))  # PQC
        ]

        print("data: ", data)

        if len(measurement) != 1:
            print(
                "Could not find measurement: ",
                fp.input,
                ", ",
                fp.measurement_start_time,
            )
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
            print(
                "Could not find measurement: ",
                fp.input,
                ", ",
                fp.measurement_start_time,
            )
            print("invalid GET request fetching measurement data")
            fp.report_ready = None
            meas_to_save.append(fp)
            continue

        # If data could not be found or a network error ocurred,
        # mark this as incomplete and process the following measurements
        if req.status_code != 200:
            print(
                "Could not find measurement: ",
                fp.input,
                ", ",
                fp.measurement_start_time,
            )
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
            input=data["input"],
            report_id=data["report_id"],
            report_filename=data.get("report_filename", "NO_AVAILABLE"),  #
            options=data.get("options", "NO_AVAILABLE"),  #
            probe_cc=data.get("probe_cc", "VE"),
            probe_asn=data["probe_asn"],
            probe_ip=data.get("probe_ip"),
            data_format_version=data["data_format_version"],
            test_name=data["test_name"],
            test_start_time=data.get("test_start_time"),
            measurement_start_time=data["measurement_start_time"],
            test_runtime=data.get("test_runtime"),
            test_helpers=data.get("test_helpers", "NO_AVAILABLE"),
            software_name=data["software_name"],
            software_version=data["software_version"],
            test_version=data["test_version"],
            bucket_date=data.get("bucket_date"),  #
            test_keys=data["test_keys"],
            annotations=data["annotations"],
        )

        fp.report_ready = True
        new_measurements.append((new_measurement, fp))
        # new_measurements.append(new_measurement)
        # meas_to_save.append(fp)

    results = {
        "success": 0,  # ammount of succesfully saved new measurements
        "error": 0,  # ammount of undetermined measurements
    }
    for fp in meas_to_save:
        results["error"] += 1
        if retrys >= 0 and fp.trys > retrys:
            fp.data_ready = FastPath.DataReady.DEAD
        else:
            fp.data_ready = FastPath.DataReady.UNDETERMINED
            fp.trys += 1

        fp.save()

    for meas, fp in new_measurements:
        try:
            meas.save()
            fp.data_ready = FastPath.DataReady.READY
            results["success"] += 1

        except Exception as e:
            print(
                "Could not save measurement: ",
                fp.input,
                ", ",
                fp.measurement_start_time,
            )
            print(
                "Could not save measurement: ",
                meas.input,
                ", ",
                meas.measurement_start_time,
            )
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


def display_top_mem_intensive_lines(
    snapshot: tracemalloc.Snapshot, limit: int = 3, key_type: str = "lineno"
):
    """Display a tracemalloc snapshot of memory usage in a given function

    Args:
        snapshot (tracemalloc.Snapshot): A snapshot with information about memory usage profiling
        key_type (str, optional): type of data to retrieve. Defaults to 'lineno'.
        limit (int, optional): Amount of top consuming lines. Defaults to 3.
    """
    snapshot = snapshot.filter_traces(
        (
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
        )
    )
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        print(
            "#%s: %s:%s: %.1f KiB" % (index, filename, frame.lineno, stat.size / 1024)
        )
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print("    %s" % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))
