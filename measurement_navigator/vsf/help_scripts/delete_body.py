"""
    This script will DELETE THE BODY FIELD in the response of every web_connectivity
    script. Be very careful with this, it's only intended for developer experience
    to ease the ammount of data stored in your local computer. This is NOT INTENDED 
    to run in a production server BY ANY MEAN.
"""
from apps.main.measurements.models import RawMeasurement
from typing import Callable, Iterable, List
import os


def delete_body(measurement: RawMeasurement):
    """
        Delete the body of a rawmeasurement and save it to db
    """
    assert measurement.test_name == "web_connectivity"
    test_keys = measurement.test_keys

    if not test_keys:
        return measurement
    if not test_keys.get("requests"):
        return measurement
    
    for r in test_keys['requests']:
        if r['response'].get("body"):
            del r['response']['body']
            r['response']['body'] = "<body removed to save space>"
    
    measurement.test_keys = test_keys
    return measurement


class Bulker:
    """
        Apply some operation to a list of elements and then save them
    """
    def __init__(self, opr : Callable[[RawMeasurement], RawMeasurement], bulk_opr : Callable[[List[RawMeasurement]], None], bulk_size : int = 500):
        self._bulk_size = bulk_size
        self._opr = opr
        self._current_bulk = []
        self._processed_count = 0
        self._bulk_opr = bulk_opr

    def add(self, measurement : RawMeasurement):
        """
            Add a new measurement to the bulker and process it if the bulk size is reached
        """
        self._current_bulk.append(self._opr(measurement))

        if self._current_bulk[-1] == None:
            print ("Wtf there's a none. My bulk is", self._current_bulk)
            exit(1)

        if len(self._current_bulk) >= self._bulk_size:
            self.flush()
        self._processed_count += 1

    def flush(self):
        """
            perform operation in current bulk
        """

        # return if nothing to do 
        if not self._current_bulk:
            return

        self._bulk_opr(self._current_bulk)
        self._current_bulk = []
        print(f"Processed {self._processed_count} measurements so far")

    def __del__(self):
        self.flush()

print("Starting body deletion procedure....")

bulker = Bulker(delete_body, lambda l: RawMeasurement.objects.bulk_update(l, ['test_keys']))
for m in RawMeasurement.objects.all().filter(test_name="web_connectivity").iterator():
    bulker.add(m)

print("Body deletion finished")