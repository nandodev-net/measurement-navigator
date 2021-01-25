# This file contains some logic function related to flags. Please do not import this file
# directly. Instead, import utils.py so you can have a public api for this functions

# Django imports:
from django.db          import connection
from django.core.cache  import cache

# Third party imports:
from typing import List
from datetime import datetime, time, timedelta

# Local imports
from .models                                import DNS, TCP, HTTP, SubMeasurement
from apps.main.measurements.flags.models    import Flag
from apps.main.events.models                import Event
from apps.main.measurements.models          import Measurement
from vsf.utils                              import CachedData, Colors as c



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
                            SELECT                  \
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
                        ms_to_update as (               \
                            SELECT DISTINCT ms.domain    \
                            FROM measurements ms \
                            WHERE NOT ms.counted\
                        ),\
                        sq as (\
                            SELECT \
                                ms.{submsmnt}_id   as id, \
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

def hard_flag(time_window : timedelta, minimum_measurements : int):
    """
        This function evaluates the measurements and flags them properly in the database
        params:
            time_window =   The time interval in which the tagged measurements should be 
                            contained
            minimum_measurements =  minimum ammount of too-near measurements to consider a hard
                                    flag
    """

    submeasurements = [(HTTP,'http'), (TCP,'tcp'), (DNS, 'dns')]

    # just a shortcut
    start_time = lambda m : m.measurement.raw_measurement.measurement_start_time

    result = {'hard_tagged':[]}
    # For every submeasurement type...
    for (SM, label) in submeasurements:

        meas = SM.objects.raw(
            (   "SELECT " +
                "submeasurements_{label}.id, " +
                "previous_counter, " +
                "rms.measurement_start_time, " +
                "dense_rank() OVER (order by rms.input) as group_id " +

                "FROM " +
                "submeasurements_{label} JOIN measurements_measurement ms ON ms.id = submeasurements_{label}.measurement_id " +
                                        "JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id " +
                                        "JOIN flags_flag f ON f.id = submeasurements_{label}.flag_id " +
                "WHERE " +
                "f.flag<>'ok' " +
                "ORDER BY rms.input, rms.measurement_start_time, previous_counter; "
            ).format(label=label)
        )

        # deprecated & slow, delete later
        # meas = SM.objects.all()\
        #             .select_related('measurement', 'measurement__raw_measurement', 'flag')\
        #             .exclude(flag=None)\
        #             .exclude(flag__flag__in=[Flag.FlagType.OK, Flag.FlagType.HARD])\
        #             .order_by(  'measurement__raw_measurement__input', 
        #                         'measurement__raw_measurement__measurement_start_time',
        #                         'previous_counter')\
        #             .values('previous_counter','id', 'measurement__raw_measurement__input')
        
        groups = filter(lambda l:len(l) >= minimum_measurements,Grouper(meas, lambda m: m.group_id))

        # A list of lists of measurements such that every measurement in an internal
        # list share the same hard flag
        tagged_meas = []

        for group in groups:
            # Search min and max
            n_meas = len(group)
            min_date = start_time(group[0])
            max_date = start_time(group[n_meas - 1])
            
            lo = 0
            hi = 0
            while min_date < max_date and hi < n_meas:
                lo = hi
                temp_max = min_date + time_window
                # search for the latest measurement whose start_time is less than temp_max
                for i in range(lo, n_meas):
                    m = group[i]
                    time = start_time(m)
                    if time > temp_max:
                        temp_max = time
                        hi = i-1
                        break
                    hi = i
                
                if hi >= n_meas:
                    hi = n_meas - 1

                # if the ammount of anomalies in that time is higher than the given counter, 
                # all those measurements should be tagged
                if group[hi].previous_counter - group[lo].previous_counter + (group[lo].flag.flag != Flag.FlagType.OK) >= minimum_measurements:
                    tagged_meas.append(filter(lambda m: m.flag.flag != Flag.FlagType.OK ,group[lo:hi+1]))
                hi += 1
                min_date = temp_max
        
        for tagged_group in tagged_meas:
            flag = Flag.objects.create(flag=Flag.FlagType.HARD)
            for m in tagged_group:
                m.flag = flag
                result['hard_tagged'].append(m)
            SM.objects.bulk_update(tagged_group, ['flag'])

    return result
            

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

def select( measurements : List[SubMeasurement],
            timedelta : timedelta = timedelta(days=1), 
            minimum_measurements : int = 7, 
            interval_size : int = 10
            ) -> List[List[SubMeasurement]]:
    """
        This aux function selects from a list of measurements
        every measurement with anomalies based on a minimum ammount of measurements
        and a time delta
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


def sug_event_creator(classname, target, asn):
    if classname == 'DNS':
        issue_type = Event.IssueType.DNS
    if classname == 'HTTP':
        issue_type = Event.IssueType.HTTP
    if classname == 'TCP':
        issue_type = Event.IssueType.TCP
    
    new_event = Event.objects.create(
        identification = classname + ' ISSUE AT '+ datetime.now().strftime('%Y-%m-%d %H:%M'),
        issue_type = issue_type,
        domain = target,
        asn = asn,
    )
    return new_event

def merge(selected_groups : List[List[SubMeasurement]]):
    """
        Given the output of "select", a list of list of submeasurements whose
        are to be merged together in the lowest ammount of hard flags possible, merge
        them by the following rules:
            1) all soft flags are merged together into a single open hard flag
            2) all hard flags are merged into a single hard flag, the earliest one
            3) closed hard flags are skiped from the logic: They are never merged to anything
    """


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

        






