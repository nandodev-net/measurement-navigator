from apps.main.measurements.submeasurements.FlagsUtils import hard_flag, count_flags_sql
from datetime import datetime

count_flags_sql()
start = datetime.now()
hard_flag()
end = datetime.now()
print((end - start).total_seconds())