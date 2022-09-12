# Django imports: 
from re import sub
from django.db import transaction
from model_utils.models import TimeStampedModel
from django.db.models import JSONField
from django.db.models.deletion import SET_NULL

# Python imports
from typing import List, Tuple, Optional
import uuid
import sys
from datetime import datetime


# local imports
from apps.main.measurements.submeasurements.models import SUBMEASUREMENTS, SubMeasurement
from apps.main.measurements.submeasurements.utils import check_submeasurement
from .models import RawMeasurement, Measurement
from vsf.utils import Colors as c

def post_save_rawmeasurement(raw : RawMeasurement, first_date : datetime):
    """Utility function to process a raw measurement not yet processed

    Args:
        raw (RawMeasurement): Measurement to process
        first_date (datetime): Logging information
    """

    if raw.is_processed:
        return # nothing to do if already processed

    # To avoid circular imports, we need to import this here:
    from .submeasurements.utils  import create_sub_measurements
    from .utils import anomaly

    print('........creating measurement from ', first_date)
    measurement = Measurement(raw_measurement=raw, anomaly=anomaly(raw))
    try:
        measurement.save()
        print(measurement.id)
    except:
        # try to delete the already stored raw measurement
        # if there was an error in somthing else
        for m in RawMeasurement.objects.filter(id=raw.id):   
            m.delete()
        return

    print('........creating la Submeasurement')
    (sub_measurements,_) = create_sub_measurements(raw)

    for sb in sub_measurements:
        sb.measurement = measurement
        try:
            sb.save() # Podemos hacer este save en lotes después
        except: 
            pass # I think we should put some loggin here @TODO
    raw.is_processed = True
    raw.save()

def create_measurement_from_raw_measurement(raw_measurement : RawMeasurement) -> Optional[Tuple[Measurement, List[SubMeasurement]]]:
    """Create the measurement object with its corresponding submeasurements. Objects are not saved to database, so 
    you should do it yourself however it fits the best with your processing structure

    Args:
        raw_measurement (RawMeasurement): Measurement to process

    Returns:
        Tuple[Measurement, List[SubMeasurement]]: List of submeasurements connected to this measurement
    """
    if raw_measurement.is_processed:
        return None # nothing to do if already processed

    # To avoid circular imports, we need to import this here:
    from .submeasurements.utils  import create_sub_measurements
    from .utils import anomaly

    measurement = Measurement(raw_measurement=raw_measurement, anomaly=anomaly(raw_measurement))
        
    (sub_measurements,_) = create_sub_measurements(raw_measurement)


    for subms in sub_measurements:
        subms.measurement = measurement

        if check_submeasurement(subms):
            subms.flag_type = SubMeasurement.FlagType.SOFT.value
        else:
            subms.flag_type = SubMeasurement.FlagType.OK.value

    return measurement, sub_measurements

class RawMeasurementBulker:
    """If you try to save a set of raw measurements, you won't be able to use the post save
    in the RawMeasurement model to generate submeasurements and measurement. This class will
    help you to create raw measurements in bulks. 

    In order to create a measurement and its submeasurements, you have to save the measurement first,
    and then the submeasurements. We do just that but in bulks, we save all measurements first, then
    submeasurements, then we mark raw measurements as processed
    """

    def __init__(self, bulk_size : int = 10000) -> None:
        self._raw_measurement_bulk = []
        self._measurement_bulk = []
        self._bulk_size = bulk_size
        self._sub_measurement_bulk = { mstype._meta.label : [] for mstype in SUBMEASUREMENTS } # Keys are model labels, values are list of instances

        # Used to iteratively generate bulk updates
        self._label_to_model_type = { mstype._meta.label : mstype for mstype in SUBMEASUREMENTS }

    @property
    def bulk_size(self) -> int:
        return self._bulk_size

    def add(self, raw_measurement : RawMeasurement, measurement : Measurement, submeasurements : List[SubMeasurement]):
        """Add the provided raw measurement and its related data to this bulker. No consistency checks are performed, so be careful 
        with what you add 

        Args:
            raw_measurement (RawMeasurement): raw measurement to be processed, it's assumed to be not processed
            measurement (Measurement): Measurement instance related to the provided measurement
            submeasurements (List[SubMeasurement]): Submeasurements related to the provided measurement instance
        """
        assert isinstance(raw_measurement, RawMeasurement)
        assert isinstance(measurement, Measurement)
        assert all(isinstance(subms, SubMeasurement) for subms in submeasurements)
        assert not raw_measurement.is_processed

        # Add measurement & raw measurement
        self._raw_measurement_bulk.append(raw_measurement)
        self._measurement_bulk.append(measurement)

        # Add submeasurements
        for sbms in submeasurements:
            model_class = type(sbms)
            model_label = model_class._meta.label
            assert model_label in self._label_to_model_type, f"type {model_class} is not a valid submeasurement type"
            self._sub_measurement_bulk[model_label].append(sbms)
        
        # Save if already reached enough raw measurements
        if len(self._raw_measurement_bulk) >= self.bulk_size:
            self._save()


    def _save(self):
        """Atomic transaction to store measurements and submeasurements in bulks
        """
        try:
            with transaction.atomic():

                # Save measurements
                Measurement.objects.bulk_create(self._measurement_bulk)

                # Save submeasurements
                for label, instances in self._sub_measurement_bulk.items():
                    self._label_to_model_type[label].objects.bulk_create(instances)

                # Save raw measurements
                for rms in self._raw_measurement_bulk:
                    rms.is_processed = True

                RawMeasurement.objects.bulk_update(self._raw_measurement_bulk, ['is_processed'])
            
        except Exception as e:
            print(c.red(f"[ERROR] Could not bulk create submeasurements. Error: {e}"), file=sys.stderr)
        
        # Reset bulks
        del self._raw_measurement_bulk
        self._raw_measurement_bulk = []

        del self._measurement_bulk
        self._measurement_bulk = []

        del self._sub_measurement_bulk
        self._sub_measurement_bulk = { mstype._meta.label : [] for mstype in SUBMEASUREMENTS }


    def __del__(self):
        self._save()    

    