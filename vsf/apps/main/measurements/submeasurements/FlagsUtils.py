# This file contains some logic function related to flags. Please do not import this file
# directly. Instead, import utils.py so you can have a public api for this functions

# Django imports:
from apps.main.sites.models import Domain
from apps.main.asns.models import ASN
from django.db          import connection
from django.core.cache  import cache

# Third party imports:
from typing import List
from datetime import datetime, timedelta
import pytz

# Local imports
from .models                                import DNS, TCP, HTTP, SubMeasurement
from apps.main.measurements.flags.models    import Flag
from apps.main.events.models                import Event
from apps.main.measurements.models          import Measurement
from vsf.utils                              import Colors as c


# FLAG COUNTING
def count_flags_sql():
    """
        This function sets the vale of "previous counter" 
        for every submeasurment according to its meaning, 
        but with raw SQL code so it should be faster
    """

    submeasurements = ['dns','http','tcp']
    with connection.cursor() as cursor:
        for subm in submeasurements:
            cursor.execute(
                (
                    "WITH \
                        measurements as (\
                            SELECT\
                                {submsmnt}.id as {submsmnt}_id, \
                                rms.measurement_start_time as start_time,\
                                {submsmnt}.flag_type as flag,\
                                ms.domain_id as domain,\
                                {submsmnt}.counted as counted,\
                                rms.probe_asn as asn,\
                                {submsmnt}.previous_counter as prev_counter\
                            FROM submeasurements_{submsmnt} {submsmnt}    JOIN measurements_measurement ms ON ms.id = {submsmnt}.measurement_id\
                                                            JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id\
                            ORDER BY domain, asn, start_time, prev_counter, {submsmnt}_id\
                        ),\
                        ms_to_update as (\
                            SELECT DISTINCT ms.domain\
                            FROM measurements ms \
                            WHERE NOT ms.counted\
                        ),\
                        sq as (\
                            SELECT \
                                ms.{submsmnt}_id   as id,\
                                ms.domain   as domain, \
                                ms.flag     as flag, \
                                SUM(CAST(ms.flag<>'ok' AS INT)) OVER (PARTITION BY ms.domain, ms.asn ORDER BY ms.start_time, ms.prev_counter, ms.{submsmnt}_id) as prev_counter\
                            FROM measurements ms JOIN ms_to_update on ms_to_update.domain = ms.domain\
                        )\
                    UPDATE submeasurements_{submsmnt} {submsmnt}\
                    SET \
                        previous_counter = sq.prev_counter,\
                        counted = CAST(1 as BOOLEAN)\
                    FROM sq\
                    WHERE {submsmnt}.id = sq.id AND (NOT counted OR {submsmnt}.previous_counter<>sq.prev_counter);"
                ).format(submsmnt=subm))

# HARD FLAG LOGIC
class Grouper():
    """
        Provides an object for lazy grouping a list of objects.
        Given an iterator sorted by some key, and the function to retrieve such key,
        provide an iterator over the groups of objects with the same key. Every iteration
        return a list of objects with the same key.
    """
    def __init__(self, queryset, get_key = lambda m: m['measurement__raw_measurement__input']):
        self.queryset_it = iter(queryset)
        self.get_key = get_key

    def __iter__(self):
        try:
            self.next_elem = next(self.queryset_it)
        except:
            self.next_elem = None
        return self
    
    def __next__(self):
        if self.next_elem is None:
            raise StopIteration
        get_input = self.get_key
        acc = []
        while True:
            acc.append(self.next_elem)
            try:
                self.next_elem = next(self.queryset_it)
            except StopIteration:
                self.next_elem = None
                if len(acc) == 0:
                    raise StopIteration
                else:
                    return acc
            if get_input(acc[0]) != get_input(self.next_elem):
                break

        return acc
    
def __bin_search_max(max_date : datetime, measurements : List[SubMeasurement], start : int, end : int) -> int:
    """
        return the index of the latest measurement within the given max_date
    """

    if start==end: return start

    # just a shortcut
    start_time = lambda m : m.measurement.raw_measurement.measurement_start_time

    for i in range(end, start - 1, -1):
        if start_time(measurements[i]) <= max_date: return i

    lo = start
    hi = end
    

    while lo < hi:
        mid = lo + (hi - lo) // 2

        if start_time(measurements[mid]) > max_date:
            hi = mid
        else:
            lo = mid
        if hi - lo == 1:
            return_hi = int(start_time(measurements[hi]) <= max_date)
            # branchless since this is hot code
            return hi * return_hi + lo * (1 - return_hi)

    return hi

def _event_creator(min_date : datetime, max_date : datetime, asn : ASN, domain : Domain, type : str) -> Event:
    """
        Helper function to create a new event
    """
    identification = f"{type} ISSUE FROM {min_date.strftime('%Y-%m-%d %H:%M:%S')} FOR ISP {asn.asn if asn else 'UNKNOWN_ASN'} ({asn.name if asn else 'UNKNOWN_ASN'})"
    return Event(
            identification=identification, 
            start_date=min_date, 
            end_date=max_date,
            domain=domain,
            asn=asn,
            issue_type=type)

def select( measurements : List[SubMeasurement],
            timedelta : timedelta = timedelta(days=1), 
            minimum_measurements : int = 7, 
            interval_size : int = 10
            ) -> List[List[SubMeasurement]]:
    """
        This aux function selects from a list of measurements
        every measurement with anomalies based on a minimum ammount of measurements
        and a time delta.
        Preconditions:
            measurements sorted by (date, previous_counter, id)
    """

    # Measurement ammount, if not enough to fill a window or an interval, return an empty list
    n_meas : int = len(measurements)

    if n_meas < minimum_measurements:
        return []

    # Resulting list
    result : List[List[SubMeasurement]] = []

    # shortcuts
    start_time = lambda m : m.measurement.raw_measurement.measurement_start_time
    anomaly_count = lambda lo, hi : measurements[hi].previous_counter -\
                                    measurements[lo].previous_counter +\
                                    (measurements[lo].flag_type != SubMeasurement.FlagType.OK)

    # Pointers to start and end positions in our measurement window
    lo : int = 0
    hi : int = min(interval_size - 1, n_meas-1)
    while n_meas - lo > minimum_measurements:
        # Search for anomaly measurements
        if measurements[lo].flag_type == Flag.FlagType.OK:
            lo += 1
            hi = min(hi+1, n_meas-1)
            continue
        max_in_date = __bin_search_max(start_time(measurements[lo]) + timedelta, measurements, lo, hi)
        n_anomalies = anomaly_count(lo, max_in_date)
        # If too many anomalies in this interval:
        if n_anomalies < minimum_measurements:
            lo += 1
            hi = min(hi+1, n_meas-1)
            continue

        # If too many anomalies, start a selecting process.
        current_block : List[Measurement] = []

        while n_anomalies > 1:

            last_index = lo
            for i in range(lo, min(max_in_date + 1, n_meas)):
                if measurements[i].flag_type != SubMeasurement.FlagType.OK:
                    current_block.append(measurements[i])
                    last_index = i

            lo = last_index
            hi = min(lo + interval_size - 1, n_meas-1)
            # search for anomaly measurements whose start time is within the given window 
            max_in_date = __bin_search_max(
                                start_time(measurements[last_index])+timedelta, 
                                measurements, 
                                lo, 
                                hi)
            n_anomalies = anomaly_count(last_index, max_in_date)

            lo = min(lo+1, n_meas-1)
            hi = min(hi+1, n_meas-1)

        result.append(current_block)

    return result

def merge(measurements_with_flags : List[SubMeasurement]):
    """
        Given the output of "select", a list of submeasurements which 
        are to be merged together in the lowest possible ammount of hard flags, merged
        by the following rules:
            1) all soft flags are merged together into a single open hard flag
            2) all hard flags are merged into a single hard flag, the earliest one
            3) closed hard flags are skiped from the logic: They are never merged to anything
    """

    # If there's no measurements, we have nothing to do here
    if not measurements_with_flags: return 

    soft_flags : List[SubMeasurement] = [] # Measurements with soft flag
    hard_flags : List[SubMeasurement] = [] # Measurements with hard flag 
    soft = SubMeasurement.FlagType.SOFT
    hard = SubMeasurement.FlagType.HARD

    start_time = lambda m: m.measurement.raw_measurement.measurement_start_time

    # Filter measurements by type
    resulting_event : Event = None
    for measurement in measurements_with_flags:
        if measurement.flag_type == soft:
            soft_flags.append(measurement)
        elif measurement.flag_type == hard and measurement.event and not measurement.event.closed:
            hard_flags.append(measurement)
            if (resulting_event is None): resulting_event = measurement.event

    # merge all hard flags as one hard flag
    min_date : datetime = datetime.now(tz = pytz.utc) + timedelta(days=1)
    max_date = datetime(year=2000, day=1, month=1, tzinfo=pytz.utc)

    # if there's no hard flag, setup a new event 
    if resulting_event is None:
        reference_measurement = measurements_with_flags[0]
        resulting_event = _event_creator(
                    min_date, 
                    min_date, 
                    reference_measurement.measurement.asn, 
                    reference_measurement.measurement.domain,
                    reference_measurement.__class__.__name__)    
        resulting_event.save()
    
    meas_to_update : List[SubMeasurement] = []
    # upgrade this measurements to hard flag
    for measurement in soft_flags:

        # Update flag type and its event
        measurement.flag_type = SubMeasurement.FlagType.HARD
        measurement.event = resulting_event

        meas_to_update.append(measurement)
        # update min date and max date
        start = start_time(measurement)
        if start < min_date:
            min_date = start
        if start > max_date:
            max_date = start

    # Iterate over hard flags setting up new event
    events_to_delete = set()
    for measurement in  hard_flags:
        if measurement.event != resulting_event:
            events_to_delete.add(measurement.event)
            measurement.event = resulting_event
            meas_to_update.append(measurement)
            measurement.flagged = True
    
    if resulting_event.end_date < max_date or resulting_event.start_date > min_date:
        resulting_event.end_date   = max(max_date, resulting_event.end_date)
        resulting_event.start_date = min(min_date, resulting_event.start_date)
        resulting_event.save()

    # Delete innecesary events
    for event in events_to_delete: event.delete()

    # Update changed measurements
    reference_measurement = measurements_with_flags[0]
    SM_types = [HTTP, TCP, DNS]
    SM_type = None
    for t in SM_types:
        if isinstance(reference_measurement, t):
            SM_type = t
    
    if SM_type is None: raise TypeError(f"ERROR, THIS IS NOT A SUBMEASUREMENT {reference_measurement}")

    SM_type.objects.bulk_update(meas_to_update, ['flag_type', 'event', 'flagged'])
    
def hard_flag(time_window : timedelta = timedelta(days=1), minimum_measurements : int = 3):
    """
        This function evaluates the measurements and flags them properly in the database
        params:
            time_window =   The time interval in which the tagged measurements should be 
                            contained
            minimum_measurements =  minimum ammount of too-near measurements to consider a hard
                                    flag
    """

    submeasurements = [(HTTP,'http'), (TCP,'tcp'), (DNS, 'dns')]

    # For every submeasurement type...
    for (SM, label) in submeasurements:

        # select every submeasurement such that partitioned by domain,
        # there's at the least one measurement in its partition that's 
        # not flagged.
        # (so we can avoid run the logic over elements not recently updated)
        meas = SM.objects.raw(  f"WITH \
                                    measurements as (\
                                        SELECT  \
                                            domain_id,\
                                            subms.id as id,\
                                            flagged,\
                                            probe_asn\
                                        FROM    \
                                            measurements_measurement ms JOIN  submeasurements_{label} subms ON ms.id=subms.measurement_id\
                                                                        JOIN  measurements_rawmeasurement rms ON ms.raw_measurement_id=rms.id        \
                                    ),\
                                    dom_to_update as (\
                                        SELECT DISTINCT \
                                            ms.domain_id as domain,  \
                                            ms.probe_asn as asn    \
                                        FROM measurements ms \
                                        WHERE NOT flagged\
                                    ),\
                                    valid_subms as (\
                                        SELECT id, probe_asn, domain_id \
                                        FROM \
                                            measurements ms JOIN dom_to_update ON dom_to_update.domain = ms.domain_id and ms.probe_asn=dom_to_update.asn\
                                    )\
                                SELECT \
                                    submeasurements_{label}.id, \
                                    submeasurements_{label}.flagged, \
                                    submeasurements_{label}.measurement_id,  \
                                    submeasurements_{label}.flag_type,\
                                    domain_id,\
                                    previous_counter,\
                                    probe_asn \
                                FROM \
                                    submeasurements_{label} JOIN valid_subms ON valid_subms.id = submeasurements_{label}.id\
                                ORDER BY domain_id, probe_asn, previous_counter, id;")
        groups = filter(
                        lambda l:len(l) >= minimum_measurements,
                        Grouper(meas.iterator(), lambda m: (m.domain_id, m.probe_asn)) #group by domain and asn
                    )
        # A list of lists of measurements such that every measurement in an internal
        # list share the same hard flag
        for group in groups:
            weird_measurements = select(group, time_window,minimum_measurements)
            for sub_group in weird_measurements:
                merge(sub_group)
        
        SM.objects.filter(flagged=False).update(flagged=True)
            






