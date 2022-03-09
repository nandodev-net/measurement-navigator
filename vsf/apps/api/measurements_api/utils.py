from matplotlib.font_manager import json_dump
from   rest_framework.views     import APIView
from rest_framework.response import Response
import requests
import json
from apps.main.measurements.models      import RawMeasurement

class GetRawMeasurementsBodyView(APIView):
    # http://cantv.net/  20220205T030009Z_webconnectivity_VE_21826_n1_6D0oDJ7BzbSFUgL3
    def get(self, request, raw_input, raw_report):
        req_data = {
            'report_id': str(raw_report),
            'input': str(raw_input),
            'full': True
        }

        ooni_body_url = 'https://api.ooni.io/api/v1/measurement_meta'

        req = requests.get(ooni_body_url, params = req_data)
        data = req.json()
        raw_measurement = json.loads(data['raw_measurement'])
        test_keys = raw_measurement['test_keys']['requests']
        body = test_keys[0]['response']['body']
        response = {'body': body}


        return Response(response ,status=req.status_code)
