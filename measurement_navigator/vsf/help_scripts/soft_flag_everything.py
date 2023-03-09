"""
Use this script to properly set up the flag of every submeasurement as a soft flag if
the measurement has the requirements of a soft flag
"""

from apps.main.measurements.submeasurements.utils import soft_flag


soft_flag(absolute=True)