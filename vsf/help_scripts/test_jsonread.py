from apps.api.fp_tables_api.s3_ingest import request_s3_meas_data
import datetime

test_types = ['tor']
first_date = (datetime.date.today() - datetime.timedelta(days=3)), 
last_date = (datetime.date.today() - datetime.timedelta(days=2)),


request_s3_meas_data(test_types, first_date[0], last_date[0])