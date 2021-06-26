import pytz
from datetime import datetime, timedelta

CARACAS = pytz.timezone('America/Caracas')

def utc_aware_date(date, sys_tz):
    aware_date = date
    if sys_tz == "2":
        aware_date = date - timedelta(hours=4, minutes=28)
    return aware_date.astimezone()