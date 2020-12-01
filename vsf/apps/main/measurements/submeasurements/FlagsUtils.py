# This file contains some logic function related to flags. Please do not import this file
# directly. Instead, import utils.py so you can have a public api for this functions

# Django imports:
from django.db.models   import Min, Max

# Third party imports:
from datetime import datetime, timedelta

# Local imports
from .models                                import DNS,TCP, HTTP,SubMeasurement
from apps.main.measurements.flags.models    import Flag
from apps.main.measurements.models          import RawMeasurement
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
            
            

def grouper(submeas : [SubMeasurement]) -> [[SubMeasurement]]:
    """
        Utility function to group together measurements of the same input
    """
    n_meas = len(submeas)
    if len(submeas) == 0:
        return []

    acc = []
    curr = [submeas[0]]
    get_input = lambda m: m['measurement__raw_measurement__input']

    for i in range(1,n_meas):
        sm = submeas[i]
        if get_input(sm) == get_input(curr[0]):
            curr.append(sm)
        else:
            acc.append(curr)
            curr = [sm]

    return acc

def hard_flag(time_window : timedelta = timedelta(days=1), minimum_measurements : int = 3):
    """
        This function evaluates the measurements and flags them properly in the database
        params:
            time_window =   The time interval in which the tagged measurements should be 
                            contained
            minimum_measurements =  minimum ammount of too-near measurements to consider a hard
                                    flag
    """
    submeasurements = [HTTP, TCP, DNS]

    # just a shortcut
    start_time = lambda m : m.measurement.raw_measurement.measurement_start_time

    result = {'hard_tagged':[]}
    # For every submeasurement type...
    for SM in submeasurements:
        meas = SM.objects.all()\
                    .select_related('measurement', 'measurement__raw_measurement', 'flag')\
                    .exclude(flag=None)\
                    .exclude(flag__flag__in=[Flag.FlagType.OK, Flag.FlagType.HARD])\
                    .order_by(  'measurement__raw_measurement__input', 
                                'measurement__raw_measurement__measurement_start_time',
                                'previous_counter')
        
        groups = filter(lambda l:len(l) >= minimum_measurements,grouper(meas))

        # A list of lists of measurements such that every measurement in an internal
        # list share the same hard flag
        tagged_meas = []

        for group in groups:
            # -- DEBUG, DELETE LATER @TODO -------+
            for m in group:
                print(  "Input: ", m.measurement.raw_measurement.input, 
                        ". Start time: ", m.measurement.raw_measurement.measurement_start_time,
                        ". Flag: ", m.flag.flag,
                        ". Counter: ", m.previous_counter)

            # ------------------------------------+


            # Search min and max
            n_meas = len(group)
            min_date = start_time(group[0])
            max_date = start_time(group[n_meas - 1])

            lo = 0
            hi = 0
            while min_date < max_date:
                lo = hi
                temp_max = min_date + time_window

                # search for the latest measurement whose start_time is less than temp_max
                for i in range(lo, n_meas):
                    m = group[i]
                    if start_time(m) > temp_max:
                        hi -= 1
                        break
                    hi += 1
                
                if hi >= n_meas:
                    hi -= 1

                # if the ammount of anomalies in that time is higher than the given counter, 
                # all those measurements should be tagged
                if group[hi].previous_counter - group[lo].previous_counter + (group[hi].flag.flag == Flag.FlagType.SOFT) >= minimum_measurements:
                    tagged_meas.append(group[lo:hi+1])

                min_date = temp_max
        
        for tagged_group in tagged_meas:
            flag = Flag.objects.create(flag=Flag.FlagType.HARD)
            for m in tagged_group:
                m.flag = flag
                m.save()
                result['hard_tagged'].append(m)

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
    