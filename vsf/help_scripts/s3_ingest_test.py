# Setup django -----------------
# import os
# os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.development'
# cwd = os.getcwd()
# import django 
# django.setup()
# -------------------------------


from os import kill
import datetime
import time
import viztracer as vzt
from apps.api.fp_tables_api.s3_ingest import S3IngestManager
from apps.api.fp_tables_api.utils import display_top_mem_intensive_lines
import signal


ini_date_str = '01-07-2022'
end_date_str = '30-07-2022'


test_types = ['tor']

first_date = datetime.datetime.strptime(ini_date_str, '%d-%m-%Y').date()
first_date_ = datetime.datetime.strptime(ini_date_str, '%d-%m-%Y').date()
last_date = datetime.datetime.strptime(end_date_str, '%d-%m-%Y').date()

delta = datetime.timedelta(days=1)
time_ini = time.time()


try:
    print('Getting measurements from: ', first_date, ' to: ', last_date)
    s3_ingestor = S3IngestManager()

    # s3_ingestor.ingest(first_date=first_date, last_date=last_date, test_types=['tor'], output_dir="/run/media/luis/Storage/ooni/", incompatible_dir="/run/media/luis/Storage/ooni_incompatible_dir/")
    s3_ingestor.ingest(first_date=first_date, last_date=last_date)

except (InterruptedError, MemoryError):
    print("Process interrupted by used")

time_end = time.time()
print('\n\nS3 TOTAL ingest time: ', time_end-time_ini)
print(first_date_, ' ', last_date)