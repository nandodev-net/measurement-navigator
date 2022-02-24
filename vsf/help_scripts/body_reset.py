"""
    This script will DELETE THE BODY FIELD in the response of every web_connectivity
    script. Be very careful with this, it's only intended for developer experience
    to ease the ammount of data stored in your local computer. This is NOT INTENDED 
    to run in a production server BY ANY MEAN.
"""
import asyncio
from apps.main.measurements.models import RawMeasurement
import os
# Safety check

print("Keep in mind that you shouldn't be running this script in a production server, this is for local development only.")

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

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
            r['response']['body'] = "<body removed to save space>"
    
    measurement.test_keys = test_keys
    measurement.save()

async def measurement_processor(name : str, queue : asyncio.Queue):
    """
        This worker will process every measurement it can, it will delete its 
        body and save it to DB.
    """
    while True:
        measurement : RawMeasurement = await queue.get()
        delete_body(measurement)
        del measurement
        queue.task_done()

async def main():
    queue = asyncio.Queue(100)
    tasks = [asyncio.create_task(measurement_processor(f"worker-{i}", queue)) for i in range(3)]

    # Enqueue measurements to be processed
    for ms in RawMeasurement.objects.all().iterator():

        if queue.full():
            print("Queue full, might need to wait until it's empty")

        await queue.put(ms)

    print("Done searching for measurements")
    # wait for the work to be done
    await queue.join()

    print("All measurements processed")
    for task in tasks:
        task.cancel()

    print("Waiting for tasks to end...")
    await asyncio.gather(*tasks, return_exceptions=True)


asyncio.run(main())