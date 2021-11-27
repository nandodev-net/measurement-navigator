import pytz
from datetime import datetime, timedelta

CARACAS = pytz.timezone('America/Caracas')

def utc_aware_date(date, sys_tz):
    aware_date = date
    if sys_tz == "2":
        if aware_date:
            aware_date = date - timedelta(hours=4, minutes=28)
        else:
            aware_date = datetime.now() - timedelta(hours=4, minutes=28)
    return aware_date.astimezone()