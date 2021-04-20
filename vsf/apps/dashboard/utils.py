import pytz

CARACAS = pytz.timezone('America/Caracas')

def utc_aware_date(date):
    aware_date = date.replace(tzinfo=CARACAS)
    return aware_date.astimezone(pytz.UTC)