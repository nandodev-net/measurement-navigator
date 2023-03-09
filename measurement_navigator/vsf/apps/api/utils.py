import pytz

def utc_aware_date(date):
    caracas = pytz.timezone('America/Caracas')
    aware_date = date.replace(tzinfo=caracas)
    return aware_date.astimezone(pytz.UTC)