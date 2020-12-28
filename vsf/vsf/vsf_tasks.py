"""
    This file imports tasks from every app, so we can easily import them where needed.
"""

from apps.api.fp_tables_api.tasks  import fp_update, measurement_update
from apps.main.measurements.submeasurements.tasks   import hard_flag_task, SoftFlagMeasurements, count_flags_submeasurements