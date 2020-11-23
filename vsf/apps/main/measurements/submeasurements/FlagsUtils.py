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
    ready_to_update = []

    # Iterate over the submeasurements types:
    for SM in submeasurements:

        # Get the data we need, all the submeasurements ordered by input, and by date
        sms = SM.objects.all()\
                .select_related('measurement', 'measurement__raw_measurement', 'flag')\
                .exclude(flag=None)\
                .order_by('measurement__raw_measurement__input', 'measurement__raw_measurement__measurement_start_time')
        
        sms_ready = []          # store ready measurements in this list:
        groups = grouper(sms)   # perform a partition over the measurements by its input
        for group in groups:
            counter = 0
            for sm in group:
                counter += sm.flag.flag == Flag.FlagType.SOFT # If this measurement is tagged, add one to counter
                sm.previous_counter = counter
                sms_ready.append(sm)

        ready_to_update.append((SM, sms_ready))

    for (SM, sms) in ready_to_update:
        SM.objects.bulk_update(sms, ["previous_counter"])
            

def grouper(submeas : [SubMeasurement]) -> [[SubMeasurement]]:
    """
        Utility function to group together measurements of the same input
    """
    acc = []
    curr = []
    get_input = lambda m: m.measurement.raw_measurement.input
    for sm in submeas:
        if len(curr) == 0 or get_input(sm) == get_input(curr[0]):
            curr.append(sm)
        else:
            acc.append(curr)
            curr = []

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
                for m in group[lo:]:
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
            



        


