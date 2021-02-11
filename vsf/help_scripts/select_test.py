from apps.main.measurements.submeasurements.FlagsUtils import *



# Get the data we need, all the submeasurements ordered by input, and by date
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
    
    groups = Grouper(meas, lambda m: m.group_id)


    for group in groups:
        #start_time = time()
        #print(group)
        result = select(group)
        #elapsed_time = time() - start_time

        #print(elapsed_time)
        print(result)

        merge(result)

        
