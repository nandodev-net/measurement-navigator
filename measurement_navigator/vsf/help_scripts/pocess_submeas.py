from apps.main.measurements.models      import RawMeasurement
from apps.main.measurements.post_save_utils import post_save_rawmeasurement
from vsf.utils import Colors as c

queryset_= RawMeasurement.objects.filter(is_processed=False)
size = len(queryset_)
current = 1
for raw_meas in queryset_.iterator(chunk_size=100):
    print(c.green(f'Processing '+str(current)+' of '+str(size)))
    post_save_rawmeasurement(raw_meas)
    current+=1