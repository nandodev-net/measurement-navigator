# We define all the logic for stats computing in this file

# Third party imports
from apps.main.measurements.models import Measurement
from datetime   import  timedelta, datetime
from typing     import  List, Tuple
from urllib     import  parse
import sys
import requests as r

# Local imports 
from vsf.settings.settings import OONI_MEASUREMENTS_URL
from vsf.utils             import Colors as c

# Defined types
url = str
asn = str

# Internal constants
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

class MeasurementMetrics:
    """
        Contains data about each measurement time interval, such as
        anomaly count, count, etc
    """    
    count         : int = 0
    anomaly_count : int = 0

    def __init__(self, count : int = 0, anomaly_count : int = 0):
        self.anomaly_count = anomaly_count
        self.count = count

    def __repr__(self) -> str:
        return f"[input : count: {self.count}, anomaly_count : {self.anomaly_count}]"

    

class DataProcessor:
    """
        Request data from ooni between a `start` date and an `end` date.
        If since is not provided, it's defaulted to today - 30 days. 
        If until is not provided, it's defaulted to since + 30 days
        If step is not provided, it's defaulted to one hour
    """
    step       : timedelta = timedelta(minutes=1)
    start_time : datetime  = None
    end_time   : datetime  = None
    results    : dict      = {}
    _probe_cc  : str       = 'VE'
    _date_format : str     = _DATE_FORMAT

    def __init__(   self, 
                    since : datetime = None, 
                    until : datetime = None, 
                    step : timedelta = timedelta(hours=1)):
        # Default values
        if since is None:
            since = datetime.now() - timedelta(days=30)
        if until is None:
            until = since + timedelta(days=30)
        
        # consistency check
        assert since < until, "'since' date should be strictly lower than 'until' date"
        
        # Clamp step so it is not bigger than provided interval
        step = min(step, until-since)

        # Init data
        self.step = step
        self.start_time = since
        self.end_time   = until

    def get(self, inputs : List[Tuple[url,asn]]):
        """
            Request data from ooni and store it in this object
        """
        for (url_inpt, asn_inpt) in inputs:
            if not self.get_measurement(url_inpt, asn_inpt):
                print(c.yellow(f"WARNING: could not retrieve data for url {url_inpt}, asn {asn_inpt}"), file=sys.stderr)
            
        pass

    def get_measurement(self, url_inpt : url, asn_inpt : asn) -> bool:
        """
            Request data from ooni for this input url and asn, return if was able to retrieve
            all data needed 
        """
        assert self.start_time and isinstance(self.start_time, datetime), "inconsistent DataProcessor object" 
        assert self.end_time   and isinstance(self.end_time,   datetime), "inconsistent DataProcessor object" 

        since = datetime.strftime(self.start_time, _DATE_FORMAT)
        until = datetime.strftime(self.end_time,   _DATE_FORMAT)

        args = {
            'since'     : since,
            'until'     : until,
            'probe_cc'  : 'VE',
            'probe_asn' : asn_inpt,
            'input'     : url_inpt,
            'order_by'  : 'measurement_start_time',
            'order'     : 'asc'
        }

        # Shortcut function to parse a measurement's start time
        get_start_time = lambda m : datetime.strptime(m['measurement_start_time'][:len(m['measurement_start_time'])-1], _DATE_FORMAT)

        next_url = OONI_MEASUREMENTS_URL + '?' + parse.urlencode(args)

        # if all request where succesfull
        success = True
        result : dict = {'total' : 0, 'total_anomaly' : 0, 'detailed' : []}

        while next_url:
            # Get ooni data
            req = r.get(next_url)

            # If could not get this url, we don't know what's the next so we end
            if req.status_code != 200:
                print(c.yellow(f"Warning: Could not retrieve measurements for url {url_inpt} with asn {asn_inpt}. Status code: {req.status_code}"), file=sys.stderr)
                next_url = None
                success = False
                continue
            
            # Get obtained data
            data = req.json()
            metadata = data['metadata']
            results  = data['results']

            # Update next url
            next_url = metadata['next_url']

            # count total data data
            result['total'] += len(results)
            result['total_anomaly'] += sum(1 for res in results if res['anomaly'])

            # If there was nothing to report, just keep going
            if not results: continue

            # get aggregated data for each valid interval
            current_metrics : MeasurementMetrics = MeasurementMetrics()
            start           : datetime = self.start_time
            end             : datetime = start + self.step 
            i               : int = 0
            while i < len(results) and start <= self.end_time:
                current_ms = results[i]
                measurement_start_time = get_start_time(current_ms)

                # If this measurement is in the current interval, count it and increase the index
                if start <= measurement_start_time <= end:
                    current_metrics.count += 1
                    current_metrics.anomaly_count += current_ms['anomaly']
                    i+=1
                else: # If no measurements in the current interval, init a new one even if we're storing an empty one
                    result['detailed'].append(current_metrics)
                    current_metrics = MeasurementMetrics()
                    start = end
                    end = start + self.step
            
        if success:
            self.results[(url_inpt, asn_inpt)] = result
        
        return success

    
    