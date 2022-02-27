# Django imports: 
from django.db import models
from model_utils.models import TimeStampedModel
from django.contrib.postgres.fields import JSONField
from django.db.models.deletion import SET_NULL

# third party imports:
import uuid
import sys

# local imports
from apps.main.sites.models         import Domain 
from apps.main.asns.models          import ASN
from .models import RawMeasurement, Measurement

def post_save_rawmeasurement(raw_list, first_date):
    # To avoid circular imports, we need to import this here:
    from .submeasurements.utils  import create_sub_measurements
    from .utils import anomaly

    for raw in raw_list:
        print('........creando la medicion ', first_date)
        measurement = Measurement(raw_measurement=raw, anomaly=anomaly(raw))
        try:
            measurement.save()
            print(measurement.id)
        except:
            # try to delete the already stored raw measurement
            # if there was an error in somthing else
            for m in RawMeasurement.objects.all(id=raw.id):   
                m.delete()
            return

        print('........creando la Submedicion')
        (sub_measurements,_) = create_sub_measurements(raw)

        for sb in sub_measurements:
            sb.measurement = measurement
            try:
                sb.save()
            except: 
                pass # I think we should put some loggin here @TODO
        raw.is_processed = True
        raw.save()