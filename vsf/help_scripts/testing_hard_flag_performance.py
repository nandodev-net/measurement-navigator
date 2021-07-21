from apps.main.measurements.submeasurements.FlagsUtils import hard_flag, count_flags_sql
from apps.configs.models    import Config
from datetime import datetime, timedelta


config = Config.objects.all().first()

if config:
    interval = timedelta(days=config.hardflag_timewindow) 
    min_meas = config.hardflag_openning_treshold
    continue_tresh = config.hardflag_continue_treshold
    interval_size = config.hardflag_interval_size
else:
    interval = timedelta(days=1)
    min_meas = 7
    interval_size = 10
    continue_tresh = 5


count_flags_sql()
start = datetime.now()
hard_flag(interval, min_meas, interval_size, continue_tresh)
end = datetime.now()
print((end - start).total_seconds())