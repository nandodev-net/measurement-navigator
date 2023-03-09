from datetime import datetime
from apps.api.fp_tables_api.utils import request_fp_data

date_format = "%Y-%m-%d"

since = datetime(year=2020,day=1,month=1).strftime(date_format)
until = datetime.now().strftime(date_format)
request_fp_data(since,until,from_fastpath = False)