# This file contains some logic function related to flags. Please do not import this file
# directly. Instead, import utils.py so you can have a public api for this functions

# Django imports:
from concurrent.futures import process
from optparse import Option
from django.db.models.query import QuerySet
from apps.main.sites.models import Domain
from apps.main.asns.models import ASN
from django.db          import connection
from django.core.cache  import cache
from django.db.models import Model, QuerySet
import sys

# Third party imports:
from typing import List, Optional, Tuple, Type
from datetime import datetime, timedelta
import pytz
import time

# Local imports
from .models                                import DNS, TCP, HTTP, TOR, SubMeasurement
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
    print(c.blue("Starting flag counting process..."))
    start_time = time.time()

    submeasurements = ['dns','http','tcp', 'tor']
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
                                ms.asn_id as asn,\
                                {submsmnt}.previous_counter as prev_counter\
                            FROM submeasurements_{submsmnt} {submsmnt}    JOIN measurements_measurement ms ON ms.id = {submsmnt}.measurement_id\
                                                            JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id\
                            ORDER BY domain, asn, start_time, prev_counter, {submsmnt}_id\
                        ),\
                        ms_to_update as (\
                            SELECT DISTINCT \
                            ms.domain, \
                            ms.asn\
                            FROM measurements ms \
                            WHERE NOT ms.counted\
                        ),\
                        sq as (\
                            SELECT \
                                ms.{submsmnt}_id   as id,\
                                ms.domain   as domain, \
                                ms.flag     as flag, \
                                SUM(CAST(ms.flag<>'ok' AS INT)) OVER (PARTITION BY ms.domain, ms.asn ORDER BY ms.start_time, ms.prev_counter, ms.{submsmnt}_id) as prev_counter\
                            FROM \
                                measurements ms JOIN ms_to_update on ms_to_update.domain = ms.domain AND ms_to_update.asn=ms.asn\
                        )\
                    UPDATE submeasurements_{submsmnt} {submsmnt}\
                    SET \
                        previous_counter = sq.prev_counter,\
                        counted = CAST(1 as BOOLEAN)\
                    FROM sq\
                    WHERE {submsmnt}.id = sq.id AND (NOT counted OR {submsmnt}.previous_counter<>sq.prev_counter);"
                ).format(submsmnt=subm))
    end_time = time.time()
    print(c.green(f"[SUCCESS] Finished flag counting process in {round(end_time - start_time, 4)}s"))

# HARD FLAG LOGIC
def grouper(queryset, key = lambda m: m['measurement__raw_measurement__input']):
    """
        Provides a generator object for lazy grouping a list of objects.
        Given an iterator sorted by some key, and the function to retrieve such key,
        provide an iterator over the groups of objects with the same key. Every iteration
        return a list of objects with the same key.
    """

    try:
        acc = [next(queryset)]
    except StopIteration:
        return []

    for elem in queryset:
        # if they have the same key, add it to the list
        if key(acc[0]) == key(elem):
            acc.append(elem)
        else:
            # otherwhise, return this element and start a new group
            yield acc
            acc = [elem]
        
    if acc: yield acc

class ModelDeleter():
    """
        Efficiently schedule deleting model elements, delete
        when count is greater than a treshold.
        model: model class to whose objects are to be deleted
        treshold: how many measurements to store before deleting (defaults to 1000)
    """
    def __init__(self, model : Type[Model], treshold : int = 1000):
        self.model = model
        self.buff  = set()
        self.treshold = treshold

    # Schedule an element to delete
    def delete(self, elem):
        self.buff.add(elem)
        if len(self.buff) > self.treshold: 
            self.flush()
        
    # actually delete scheduled objects
    def flush(self):
        ids = map(lambda m: m.id, self.buff)
        self.model.objects.filter(id__in=list(ids)).delete()
        self.buff = set()

    # delete all before destroy
    def __del__(self):
        self.flush()

def _bin_search_max(indexable, upper_bound, start : int = 0, end : int = None, key = lambda x : x) -> int:
    print("Running binary search")
    lo : int = start
    hi : int = end or (len(indexable) - 1)

    while lo < hi:
        mid = lo + (hi - lo) // 2

        if key(indexable[mid]) <= upper_bound:
            lo = mid
        else:
            hi = mid

        if hi - lo == 1: break

    return hi if key(indexable[hi]) <= upper_bound else lo

def _event_creator(min_date : datetime, max_date : datetime, asn : ASN, domain : Domain, type : str) -> Event:
    """
        Helper function to create a new event
    """
    print("Creating event")
    identification = f"{type} ISSUE FROM {min_date.strftime('%Y-%m-%d %H:%M:%S')} FOR ISP {asn.asn if asn else 'UNKNOWN_ASN'} ({asn.name if asn else 'UNKNOWN_ASN'})"
    return Event(
            identification=identification, 
            start_date=min_date,
            current_start_date=min_date, 
            end_date=max_date,
            current_end_date=max_date,
            domain=domain,
            asn=asn,
            issue_type=type)

def select( measurements : List[SubMeasurement],
            timedelta : timedelta = timedelta(days=1), 
            event_openning_treshold : int = 1, 
            interval_size : int = 5,
            event_continue_treshold : int = 5
            ) -> List[List[SubMeasurement]]:
    """
        This aux function selects from a list of measurements
        every measurement with anomalies based on a minimum ammount of measurements
        and a time delta.
        Preconditions:
            measurements sorted by (date, previous_counter, id)
        Params:
            measurements : some measurements iterable and indexable container = measurements to groups
            timedelta    : timedelta = how much time to consider when expanding events
            event_openning_treshold : int = how many anomaly measurements are required to open a new event
            interval_size : int = maximum ammount of measurements to consider when inspecting a possible event start
            event_continue_treshold : int = how many anomaly measurements are required to expand an existent event with new measurements
        Return:
            A list of lists containing measurements that may be grouped together as a single event
    """
    print("Running Select Function")
    # Check input
    assert interval_size > 0, "Interval size should be a possitive number"
    assert event_openning_treshold > 0, "Minimum ammount of measurements to open an event should be a possitive number"
    assert event_continue_treshold <= event_openning_treshold, "Continuation treshold should be less than or equal openning treshold"
    assert event_continue_treshold > 0, "Continuation treshold should be a possitive number"
    assert event_openning_treshold <= interval_size

    # Measurement amount, if not enough to fill a window or an interval, return an empty list
    n_meas : int = len(measurements)
    if n_meas < event_openning_treshold:
        return []
    # Resulting list
    # result : List[List[SubMeasurement]] = []
    # shortcuts
    start_time = lambda m : m.start_time
    anomaly_count = lambda lo, hi : measurements[hi].previous_counter -\
                                    measurements[lo].previous_counter +\
                                    (measurements[lo].flag_type != SubMeasurement.FlagType.OK)

    # Pointers to start and end positions in our measurement window
    lo : int = 0
    hi : int = min(interval_size - 1, n_meas-1)
    while n_meas - lo > event_openning_treshold:
        # Search for anomaly measurements
        if measurements[lo].flag_type == Flag.FlagType.OK:
            measurements[lo] = None
            lo += 1
            hi = min(hi+1, n_meas-1)
            continue

        # if you get a measurement with anomalies, check between lo, hi to see whether there's more than event_openning_treshold
        # anomalies
        max_in_date = _bin_search_max(measurements, start_time(measurements[lo]) + timedelta, lo, hi, start_time)
        n_anomalies = anomaly_count(lo, max_in_date)
        # If too many anomalies in this interval:
        if n_anomalies < event_openning_treshold:
            lo += 1
            hi = min(hi+1, n_meas-1)
            continue

        # import os, psutil
        # process = psutil.Process(os.getpid())
        # print("memoy: ", process.memory_info().rss / 1000000)
        # If too many anomalies, start a selecting process.
        current_block : List[Measurement] = []
        while n_anomalies > event_continue_treshold:
            print(c.green(f"\t Taking from {measurements[lo].start_time} to {measurements[max_in_date].start_time}"))
            last_index = lo
            for i in range(lo, min(max_in_date + 1, n_meas)):
                if measurements[i].flag_type != SubMeasurement.FlagType.OK:
                    # print(c.blue(f"\t added {measurements[i].id}, flag: {measurements[i].flag_type}, "))
                    current_block.append(measurements[i])
                    # print(current_block)
                    last_index = i

            lo = last_index
            hi = min(lo + interval_size - 1, n_meas-1)
            # search for anomaly measurements whose start time is within the given window 
            #print('**search for anomaly measurements whose start time is within the given window ')
            max_in_date = _bin_search_max(
                                measurements, 
                                start_time(measurements[last_index]) + timedelta, 
                                lo, 
                                hi,
                                start_time)

            n_anomalies = anomaly_count(last_index, max_in_date)
            print(c.blue(f"next anomalie count: {n_anomalies}"))

            lo = min(lo+1, n_meas-1)
            hi = min(hi+1, n_meas-1)

        yield(current_block)
    print(c.green("[SUCCESS] Finished selection algorithm"))

    

def merge(measurements_with_flags : List[SubMeasurement]):
    """
        Given the output of "select", a list of submeasurements which 
        are to be merged together in the lowest possible ammount of hard flags, merged
        by the following rules:
            1) all soft flags are merged together into a single open hard flag
            2) all hard flags are merged into a single hard flag, the earliest one
            3) closed hard flags are skiped from the logic: They are never merged to anything
    """
    print(c.blue("Running merge function"))

    # If there's no measurements, we have nothing to do here
    if not measurements_with_flags: 
        print(c.green("[SUCCESS] no measurements to process, so merge process ended before started"))
        return 

    soft_flags : List[SubMeasurement] = [] # Measurements with soft flag
    hard_flags : List[SubMeasurement] = [] # Measurements with hard flag 
    soft = SubMeasurement.FlagType.SOFT
    hard = SubMeasurement.FlagType.HARD
    muted = SubMeasurement.FlagType.MUTED

    start_time = lambda m: m.start_time

    # Filter measurements by type
    resulting_event : Optional[Event] = None
    for measurement in measurements_with_flags:
        if measurement.flag_type == soft:
            soft_flags.append(measurement)
        elif measurement.flag_type == hard and measurement.event and not measurement.event.confirmed:
            hard_flags.append(measurement)
            if resulting_event is None: resulting_event = measurement.event
        elif measurement.flag_type == muted:
            continue

    # merge all hard flags as one hard flag
    min_date : datetime = datetime.now(tz = pytz.utc) + timedelta(days=1)
    max_date = datetime(year=2000, day=1, month=1, tzinfo=pytz.utc)

    # if there's no hard flag, setup a new event 
    if resulting_event is None:
        reference_measurement = measurements_with_flags[0]
        resulting_event = _event_creator(
                    reference_measurement.measurement_start_time, 
                    measurements_with_flags[-1].measurement_start_time, 
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
        measurement.flagged = True

        meas_to_update.append(measurement)
        # update min date and max date
        start = start_time(measurement)
        if start < min_date:
            min_date = start
        if start > max_date:
            max_date = start

    # Iterate over hard flags setting up new event
    events_to_delete = ModelDeleter(Event)
    for measurement in  hard_flags:
        if measurement.event != resulting_event:
            events_to_delete.delete(measurement.event)
            measurement.event = resulting_event
            meas_to_update.append(measurement)
            measurement.flagged = True
    
    if resulting_event.end_date < max_date or resulting_event.start_date > min_date:
        resulting_event.end_date   = max(max_date, resulting_event.end_date)
        resulting_event.start_date = min(min_date, resulting_event.start_date)

        if not resulting_event.end_date_manual:
            resulting_event.current_end_date = resulting_event.end_date
        if not resulting_event.start_date_manual:
            resulting_event.current_start_date = resulting_event.start_date

        resulting_event.save()

    # Update changed measurements
    reference_measurement = measurements_with_flags[0]
    SM_types = [HTTP, TCP, DNS, TOR]
    SM_type = None
    for t in SM_types:
        if isinstance(reference_measurement, t):
            SM_type = t
    
    if SM_type is None: raise TypeError(f"ERROR, THIS IS NOT A SUBMEASUREMENT {reference_measurement}")
    
    print(c.blue("Updating new event information to database..."))
    SM_type.objects.bulk_update(meas_to_update, ['flag_type', 'event', 'flagged'])
    print(c.green("[SUCCESS] Successfully finished merge function"))

    
def hard_flag(
            time_window : timedelta = timedelta(days=15.5), 
            event_openning_treshold : int = 7, #cantidad de mediciones para que, dentro del time, se cree evento
            interval_size : int = 10, # numero de mediciones hacia atras, parado en medicion con flag en medicion con flag
            event_continue_treshold : int = 5
            ):
    """
        This function evaluates the measurements and flags them properly in the database
        params:
            time_window =   The time interval in which the tagged measurements should be 
                            contained
            event_openning_treshold =  minimum ammount of too-near measurements to consider a hard
                                        flag
            interval_size = how many measurements to consider in each step of the algorithm

            event_continue_treshold : int = how many anomaly measurements are required to expand an existent event with new measurements

    """
    
    submeasurements : List[Tuple[Type[Model], str]] = [(DNS,'dns'), (HTTP,'http'), (TCP,'tcp'), (TOR,'tor')]
    
    # For every submeasurement type...
    print(c.blue("Starting hard flag process"))

    # for timing
    start = time.time()

    for (SM, label) in submeasurements:
        # select every submeasurement such that partitioned by (domain, asn),
        # there's at the least one measurement in its partition that's 
        # not flagged.
        # (so we can avoid run the logic over elements not recently updated)
        print(c.blue(f"Requesting submeasurements of type: {label}"))
        meas = SM.objects.raw(  f"WITH \
                                    measurements as (\
                                        SELECT  \
                                            domain_id,\
                                            subms.id as id,\
                                            flagged,\
                                            ms.asn_id as probe_asn,\
                                            raw_measurement_id\
                                        FROM    \
                                            measurements_measurement ms JOIN  submeasurements_{label} subms ON ms.id=subms.measurement_id\
                                    ),\
                                    dom_to_update as (\
                                        SELECT DISTINCT \
                                            ms.domain_id as domain,  \
                                            ms.probe_asn as asn    \
                                        FROM measurements ms \
                                        WHERE NOT flagged\
                                    ),\
                                    valid_subms as (\
                                        SELECT id, probe_asn, domain_id, raw_measurement_id \
                                        FROM \
                                            measurements ms JOIN dom_to_update ON dom_to_update.domain = ms.domain_id AND ms.probe_asn=dom_to_update.asn\
                                    )\
                                SELECT \
                                    submeasurements_{label}.id, \
                                    submeasurements_{label}.flagged, \
                                    submeasurements_{label}.measurement_id,  \
                                    submeasurements_{label}.flag_type,\
                                    domain_id,\
                                    previous_counter,\
                                    valid_subms.probe_asn as probe_asn, \
                                    rms.measurement_start_time as start_time\
                                FROM \
                                    submeasurements_{label} JOIN valid_subms ON valid_subms.id = submeasurements_{label}.id\
                                                            JOIN measurements_rawmeasurement rms ON rms.id=raw_measurement_id\
                                ORDER BY domain_id, probe_asn, start_time asc, previous_counter;")

        groups = filter(
                        lambda l:len(l) >= event_openning_treshold,
                        grouper(meas.iterator(), lambda m: (m.domain_id, m.probe_asn)) #group by domain and asn
                    )

        # A list of lists of measurements such that every measurement in an internal
        # list share the same hard flag
        print(c.blue("Starting grouping and selection process"))
        for group in groups:

            weird_measurements = select(group, time_window, event_openning_treshold, interval_size, event_continue_treshold)
            for sub_group in weird_measurements:
                merge(sub_group)
                del(sub_group)

        
        SM.objects.filter(flagged=False).update(flagged=True)

    end = time.time()
    print(c.green(f"[SUCCESS] Finished hard flag process in {round(end-start, 4)} s"))

    return { 
        'arguments' : {
            'interval_size' : interval_size,
            'event_openning_treshold' : event_openning_treshold,
            'event_continue_treshold' : event_continue_treshold,
            'time_window' : str(time_window)
        }
    }
            
def update_event_dates():
    """
        Update start_date, end_date fields in 
        event table following dates in its 
        related submeasurements 
    """
    submeasurements = ['dns','http','tcp','tor']
    with connection.cursor() as cursor:
        for subm in submeasurements:
            cursor.execute(f"WITH\
                            eventsXmeasurement as (\
                                SELECT DISTINCT\
                                    ev.id AS event_id,\
                                    ms.raw_measurement_id AS rms_id\
                                FROM events_event ev JOIN submeasurements_{subm} subms         ON  subms.event_id=ev.id\
                                                        JOIN measurements_measurement ms       ON subms.measurement_id=ms.id    \
                            ),\
                            events_min_max_date as (\
                                SELECT  ev.event_id as event_id, \
                                        min(rms.measurement_start_time) as min_date, \
                                        max(rms.measurement_start_time) as max_date \
                                FROM eventsXmeasurement ev JOIN measurements_rawmeasurement rms   ON ev.rms_id=rms.id\
                                GROUP BY ev.event_id\
                            )\
                            update events_event ev\
                            SET \
                                start_date=events_min_max_date.min_date,\
                                end_date=events_min_max_date.max_date,\
                                current_start_date = CASE WHEN manual_start_time=FALSE THEN events_min_max_date.min_date,\
                                current_end_date = CASE WHEN manual_end_time=FALSE THEN events_min_max_date.max_date\
                            FROM events_min_max_date\
                            WHERE ev.id = events_min_max_date.event_id;"
                        )
    
    # now try to update title for every event
    events = Event.objects.all().select_related("asn")

    for event in events:
        event.identification = event.generate_title()
        event.save()