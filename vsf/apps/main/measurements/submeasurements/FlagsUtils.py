# This file contains some logic function related to flags. Please do not import this file
# directly. Instead, import utils.py so you can have a public api for this functions

# Django imports:
from time import timezone
from django.db.models.expressions import OrderBy
from apps.main.sites.models import Domain
from apps.main.asns.models import ASN
from django.db          import connection
from django.core.cache  import cache

# Third party imports:
from typing import List
from datetime import datetime, time, timedelta, tzinfo
import pytz

# Local imports
from .models                                import DNS, TCP, HTTP, SubMeasurement
from apps.main.measurements.flags.models    import Flag
from apps.main.events.models                import Event
from apps.main.measurements.models          import Measurement
from vsf.utils                              import CachedData, Colors as c


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
                                f.flag as flag,\
                                ms.domain_id as domain,\
                                {submsmnt}.counted as counted,\
                                rms.probe_asn as asn,\
                                {submsmnt}.previous_counter as prev_counter\
                            FROM submeasurements_{submsmnt} {submsmnt}    JOIN measurements_measurement ms ON ms.id = {submsmnt}.measurement_id\
                                                            JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id\
                                                            JOIN flags_flag f ON f.id = {submsmnt}.flag_id\
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

def count_flags():
    """
        This function sets the value of "previous counter"
        for every submeasurement according to its meaning
    """

    submeasurements = [DNS, TCP, HTTP]

    # Iterate over the submeasurements types:
    for SM in submeasurements:

        # Get the data we need, all the submeasurements ordered by input, and by date
        sms = SM.objects.all()\
                .select_related('measurement', 'measurement__raw_measurement', 'flag')\
                .exclude(flag=None)\
                .order_by('measurement__raw_measurement__input', 'measurement__raw_measurement__measurement_start_time')\
                .values('measurement__raw_measurement__input', 'id', 'flag__flag')
        groups = Grouper(sms)   # perform a partition over the measurements by its input
        for group in groups:
            print(group[0]['measurement__raw_measurement__input'], " : ", len(group))
            sms_ready = []          # store ready measurements in this list:
            counter = 0
            for sm in group:
                counter += sm['flag__flag'] == Flag.FlagType.SOFT # If this measurement is tagged, add one to counter
                sm['previous_counter'] = counter
                sms_ready.append(sm)
        
            # Save the currently updated group
            for m in sms_ready:
                instance = SM.objects.get(id=m['id'])
                instance.previous_counter = m['previous_counter']
                instance.save()

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
    lo = start
    hi = end
    
    # just a shortcut
    start_time = lambda m : m.measurement.raw_measurement.measurement_start_time

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
                                    (measurements[lo].flag.flag != Flag.FlagType.OK)

    # Pointers to start and end positions in our measurement window
    lo : int = 0
    hi : int = min(interval_size - 1, n_meas-1)
    while n_meas - lo > minimum_measurements:
        # Search for anomaly measurements
        if measurements[lo].flag.flag == Flag.FlagType.OK:
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
                if measurements[i].flag.flag != Flag.FlagType.OK:
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

    soft_flags : List[SubMeasurement] = [] # Measurements with soft flag
    hard_flags : List[SubMeasurement] = [] # Measurements with hard flag 
    soft = Flag.FlagType.SOFT
    hard = Flag.FlagType.HARD

    start_time = lambda m: m.measurement.raw_measurement.measurement_start_time

    # Filter measurements by type
    for measurement in measurements_with_flags:
        if measurement.flag.flag == soft:
            soft_flags.append(measurement)
        elif measurement.flag.flag == hard and measurement.flag.event and not measurement.flag.event.closed:
            hard_flags.append(measurement)

    # Don't delete the same flags twice
    flags_to_delete = set()

    # merge all hard flags as one hard flag
    min_date : datetime = datetime.now(tz = pytz.utc) + timedelta(days=1)
    max_date = datetime(year=2000, day=1, month=1, tzinfo=pytz.utc)

    if hard_flags:
        # Merge all merge-able measurements to the first hard flag
        resulting_flag = hard_flags[0].flag

        for measurement in hard_flags:
            if measurement.flag.id != resulting_flag.id:
                flags_to_delete.add(measurement.flag)
            
            # Update flag field
            measurement.flag = resulting_flag
            measurement.save()

            # update min date and max date
            start = start_time(measurement)
            if start < min_date:
                min_date = start
            if start > max_date:
                max_date = start
    else:
        resulting_flag = Flag.objects.create(flag=hard)

    # upgrade this measurements to hard flag
    for measurement in soft_flags:
        flags_to_delete.add(measurement.flag)
        measurement.flag = resulting_flag
        measurement.save()

        # update min date and max date
        start = start_time(measurement)
        if start < min_date:
            min_date = start
        if start > max_date:
            max_date = start

    # Update event 
    if resulting_flag.event is None:
        reference_measurement = measurements_with_flags[0]
        event = _event_creator(
                    min_date, 
                    max_date, 
                    reference_measurement.measurement.asn, 
                    reference_measurement.measurement.domain,
                    reference_measurement.__class__.__name__)    
    else:
        event = resulting_flag.event
        event.end_date = max(max_date, resulting_flag.Event.end_date)
        
    
    event.save()
    resulting_flag = event
    resulting_flag.save()

    # Delete irrelevant flags
    for flag in flags_to_delete: 
        if flag.event:
            flag.event.delete()
        flag.delete()

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

        
        meas = SM.objects.all()\
                    .select_related('measurement', 'measurement__raw_measurement', 'flag')\
                    .exclude(flag__flag=Flag.FlagType.OK)\
                    .order_by(
                        'measurement__domain', 
                        'measurement__raw_measurement__probe_asn', 
                        'measurement__raw_measurement__measurement_start_time',
                        'previous_counter',
                        'id')

        groups = filter(
                        lambda l:len(l) >= minimum_measurements,
                        Grouper(meas, lambda m: (m.measurement.domain.id, m.measurement.raw_measurement.probe_asn)) #group by domain and asn
                    )
        # A list of lists of measurements such that every measurement in an internal
        # list share the same hard flag
        for group in groups:
            weird_measurements = select(group, time_window,minimum_measurements)
            for sub_group in weird_measurements:
                merge(sub_group)

    return
            


def sug_event_creator(classname, target, asn):
    if classname == 'DNS':
        issue_type = Event.IssueType.DNS
    if classname == 'HTTP':
        issue_type = Event.IssueType.HTTP
    if classname == 'TCP':
        issue_type = Event.IssueType.TCP
    
    new_event = Event.objects.create(
        identification = classname + ' ISSUE AT '+ datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        issue_type = issue_type,
        domain = target,
        asn = asn,
    )
    return new_event



def merge_old(select_groups):

    target_list = []

    if not select_groups: return

    for group in select_groups:

        if group[0].flag.flag == 'soft':
            target = group[0].measurement.domain
            asn = target_list[0][0].measurement.asn
            new_sug_event = sug_event_creator(str(group[0].__class__.__name__).upper(), target, asn)
            new_hard_flag = Flag.objects.create(flag=Flag.FlagType.HARD, event=new_sug_event)
            print('HardFlag creada: ', new_hard_flag.id)

            for submeas in group:
                print('Submedicion: ', submeas.id)
                print('DeadFlag: ', submeas.flag.id)
                Flag.objects.get(id=submeas.flag.id).delete()
                submeas.flag=new_hard_flag
                print('HardFlag asignada: ', submeas.flag.id)
                submeas.save()

        elif group[0].flag.flag == 'hard' and not group[0].flag.confirmed:
            target_list.append(group)


    if target_list:

        target = target_list[0][0].measurement.domain
        asn = target_list[0][0].measurement.asn
        new_sug_event = sug_event_creator(str(group[0].__class__.__name__).upper(), target, asn)
        new_hard_flag = Flag.objects.create(flag=Flag.FlagType.HARD, event=new_sug_event)
        print('HardFlagHF creada: ', new_hard_flag.id)

        for group in target_list:
            for submeas in group:
                print('Submedicion Hf: ', submeas.id)
                print('DeadFlag Hf: ', submeas.flag.id)
                try:
                    Event.objects.get(id=submeas.flag.event.id).delete()
                except:
                    pass

                try:
                    Flag.objects.get(id=submeas.flag.id).delete()
                except:
                    pass
                submeas.flag=new_hard_flag
                print('HardFlag asignada Hf: ', submeas.flag.id)
                submeas.save()

        






