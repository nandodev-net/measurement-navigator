from django.core.paginator import Paginator
from apps.main.measurements.models      import RawMeasurement
from apps.main.measurements.post_save_utils import post_save_rawmeasurement


paginator = Paginator(RawMeasurement.objects.filter(is_processed=False).order_by('test_start_time'), 500)
for page in range(1, paginator.num_pages + 1):
    raw_list_to_process = paginator.page(page).object_list
    post_save_rawmeasurement(raw_list_to_process)