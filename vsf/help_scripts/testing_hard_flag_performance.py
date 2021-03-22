from apps.main.measurements.submeasurements.FlagsUtils import hard_flag, count_flags_sql
from apps.configs.models    import Config
from datetime import datetime, timedelta


config = Config.objects.all().first()

if config:
    interval = timedelta(days=config.hardflag_timewindow) 
    min_meas = config.hardflag_minmeasurements
    interval_size = config.hardflag_interval_size
else:
    interval = timedelta(days=1)
    min_meas = 7
    interval_size = 10


count_flags_sql()
start = datetime.now()
hard_flag(interval, min_meas, interval_size)
end = datetime.now()
print((end - start).total_seconds())