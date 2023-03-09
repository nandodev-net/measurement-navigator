"""
    This script will DELETE THE BODY FIELD in the response of every web_connectivity
    script. Be very careful with this, it's only intended for developer experience
    to ease the ammount of data stored in your local computer. This is NOT INTENDED 
    to run in a production server BY ANY MEAN.
"""
from apps.main.measurements.models import RawMeasurement
from django.core.paginator import Paginator


def delete_body(measurement: RawMeasurement):
    """
        Delete the body of a rawmeasurement and save it to db
    """
    assert measurement.test_name == "web_connectivity"
    test_keys = measurement.test_keys

    if not test_keys:
        return
    if not test_keys.get("requests"):
        return 
    
    for r in test_keys['requests']:
        if r['response'].get("body"):
            del r['response']['body']
            r['response']['body'] = "\{ 'body': 'None'\}"
    
    measurement.test_keys = test_keys
    measurement.save()



paginator = Paginator(RawMeasurement.objects.all().order_by('test_start_time'), 200)
for page in range(1, paginator.num_pages + 1):
    raw_list_to_process = paginator.page(page).object_list
    for raw_meas in raw_list_to_process:
        try:
            delete_body(raw_meas)
            print('borrado: ', str(raw_meas.id))
        except:
            print('saltado', str(raw_meas.id))
            pass
