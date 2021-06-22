import pytz

CARACAS = pytz.timezone('America/Caracas')

def utc_aware_date(date, sys_tz):
    aware_date = date
    print(date)
    if sys_tz == 2:
        aware_date = date.replace(tzinfo=CARACAS)
    return aware_date.astimezone(pytz.UTC)