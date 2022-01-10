"""
    This script is intended to be an utility to refill the database in case of 
    reinstalling it. Use this whenever you want to restore the database.

    These are the steps that are to be performed:
        - Request data from the fast path
        - apply the previous counting query
        - apply the hard flag process
"""
# Local imports
from apps.api.fp_tables_api.utils import request_fp_data # To request data from the fastpath

# Third party imports 
from datetime                     import datetime, timedelta
import time

# --- Request data from ooni --- #

print("Requesting ooni data")


today = datetime.now()
now = today - timedelta(days=4) 
n_months_ago = today - timedelta(days=5) 
now = now.strftime("%Y-%m-%d") 
n_months_ago = n_months_ago.strftime("%Y-%m-%d")

print('Since: ', n_months_ago, ' at 00:00 To: ', now,' at 00:00')
# ASNs

asn_list = [
    'AS8048', #cantv
    'AS27717' #digitel
]

inicio = time.time()
for current_asn in asn_list:
    request_fp_data(test_name='web_connectivity',since=n_months_ago, until=now, from_fastpath=False, probe_asn=current_asn)
fin = time.time()

print('Tiempo de ejecucion API: ', str(fin-inicio))
# ------------------------------ #