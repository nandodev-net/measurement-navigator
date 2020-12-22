from apps.main.measurements.submeasurements.FlagsUtils import *


submeasurements = [DNS, TCP, HTTP]

# Iterate over the submeasurements types:
for SM in submeasurements:

    # Get the data we need, all the submeasurements ordered by input, and by date
    sms = SM.objects.all()\
            .select_related('measurement', 'measurement__raw_measurement', 'flag')\
            .exclude(flag=None)\
            .order_by('measurement__raw_measurement__input', 'measurement__raw_measurement__measurement_start_time')\
            .values('measurement__raw_measurement__input', 'id', 'flag__flag')
    groups = Grouper(sms) 

    for group in groups:
        start_time = time()
        result = select(group)
        elapsed_time = time() - start_time

        print(elapsed_time)
        print(result)
        break
