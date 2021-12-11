from django.conf        import settings
import datetime as dt
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from urllib.parse import SplitResult
from pathlib import PosixPath
import posixpath


_BUCKET = 'ooni-data-eu-fra'
_PREFIX = 'raw/'


def s3_measurements_download(test_type:str='webconnectivity', country:str='VE', 
    first_date:str=(dt.date.today() - dt.timedelta(days=3)), 
    last_date:str=(dt.date.today() - dt.timedelta(days=2)),
    output_dir:str='./media/ooni_data/'):

    print('Since: ', first_date, ' at 00:00 To: ', last_date,' at 00:00')

    conn = boto3.client(
                's3', config=Config(signature_version=UNSIGNED))

    paginator = conn.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=_BUCKET, Delimiter='/', Prefix=_PREFIX,
                            StartAfter=f'{_PREFIX}{first_date.strftime("%Y%m%d")}')

    for page in pages:
        for entry in page.get('CommonPrefixes', []):
            date_dir = entry['Prefix']
            date_str = posixpath.basename(posixpath.dirname(date_dir))
            date = dt.datetime.strptime(date_str, "%Y%m%d").date()
            if date >= last_date:
                break
            for hour in range(25):
                prefix = f'''{date_dir}{hour:02}/{country}/'''
                if test_type:
                    prefix += f'{test_type}/'
                for page in paginator.paginate(Bucket=page['Name'], Prefix=prefix):
                    for entry in page.get('Contents', []):
                        key = entry['Key']
                        file_path = PosixPath(key)
                        if file_path.name.endswith('.jsonl.gz'):
                            print('Downloading Gzip file: ',file_path)
                            file_test_type = file_path.parent.name
                            url = SplitResult(
                                        's3', page['Name'], key, None, None)
                            conn.download_file(url.netloc, url.path, output_dir+url.path.replace(prefix, ''))
