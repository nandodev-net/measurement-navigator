"""
    This is a manager class useful to compute aggregated data,
    specially intended to be used in the histogram page
"""
# Django imports
from django.db import connection
from django.db.models import Count

# Python imports 
from datetime import datetime
import enum
import dataclasses
from typing import List, Dict, Union, Tuple
from collections import namedtuple

# Local imports 
from apps.main.measurements.submeasurements.models import SubMeasurement, SubmeasurementType, INSTALLED_SUBMEASUREMENTS

class ListEnum(enum.Enum):
    """
        Enum class for VSF, provides value listing
    """

    @classmethod
    def values(cls) -> List[str]:
        """
            return a list with possible values for this enum
        """
        return [x.value for x in cls]

class BlockType(ListEnum):
    """
        Possible blocks to query for aggregated data. **This is how the data is partitioned**
    """
    DAYS = "days"
    ASN = "asn"
    MEASUREMENT_TYPE = "measurement_type"
    INPUT = "input"
    SUBMEASUREMENT_TYPE = "submeasurement_type" # Only available to get information about submeasurements

@dataclasses.dataclass
class Block:
    """
        Value for a single unit returned by an agregation operation. For example, if 
        you request aggregated by day, the result should be a list of days, and this is the value returned 
        in each day
    """
    # Depends on the block type, if "days", then it will be a tuple of datetimes (start, end). 
    # Else, it will be a string with a value corresponding to the block type
    block_value : Union[str, datetime]
    data : Dict[str, int]

@dataclasses.dataclass
class AggregationResult:
    """
        Result of an aggregated operation
    """
    block_type : BlockType
    results : List[Block]


class DataAggregator:
    """
        Use this class to make aggregated queries over the mesurements types
    """

    def get_anomaly_count(self, start_date : datetime, end_date : datetime, block_type : Union[BlockType, str] = BlockType.DAYS, ) -> AggregationResult:
        """
            Get the aggregation summary for measurements.
            Returned data for each block looks like this:
                {
                    "anomaly_true" : int,
                    "anomaly_false": int
                }
        """

        if isinstance(block_type, (BlockType, str)):
            block_type = BlockType(block_type)
        
        if block_type == BlockType.SUBMEASUREMENT_TYPE:
            raise ValueError("Provided block type is not a valid one because it is a submeasurement block type, which is not supported in this query")

        # This dict will map from block type to the corresponding aggregation column, 
        # like day, asn, measurement type or input
        block_mapper = {
            BlockType.DAYS : "date_trunc('day', rms.measurement_start_time)",
            BlockType.ASN  : "rms.probe_asn",
            BlockType.MEASUREMENT_TYPE : "rms.test_name",
            BlockType.INPUT : "rms.input"
        }

        # TODO considerar también issue type cuando se nos pide conteo de flags

        # Check for null only when requesting data about input
        query = f"SELECT {block_mapper[block_type]} AS block, ms.anomaly as anomaly, count(ms.anomaly) as anomaly_count\
                    FROM measurements_measurement ms JOIN measurements_rawmeasurement rms ON ms.raw_measurement_id=rms.id \
                    WHERE rms.measurement_start_time > %s AND rms.measurement_start_time < %s\
                    {'AND  rms.input IS NOT NULL' if block_type == BlockType.INPUT else ''}\
                    GROUP BY (block, anomaly) \
                    ORDER BY block, ms.anomaly;"
        
        with connection.cursor() as cursor:
            cursor.execute(query, [start_date, end_date])
            # Create a dict, so the fields have names too
            col_names = [col[0] for col in cursor.description]
            results = [dict(zip(col_names, row)) for row in cursor.fetchall()]

        # Function to control how the block data is updated
        def update_block_content(block : dict, row_data : dict) -> dict:
            row_data['anomaly_true' if block['anomaly'] else 'anomaly_false'] = block['anomaly_count']
            return row_data

        # Group blocks that are the same
        blocks = {}
        for result in results:
            block = result['block']
            blocks[block] = update_block_content(result, blocks.get(block) or {"anomaly_true" : 0, "anomaly_false" : 0})

        return AggregationResult(
            block_type, 
            [Block(value, data) for (value, data) in blocks.items()]
            )


    def get_flag_count_per_subms(self, start_time : datetime, end_time : datetime) -> AggregationResult:
        """
            Get the aggregation result for sub measurements, 
            counting how many flags of each type there is for every sub measurement
            type.
            For example:
            {
                "web_connectivity" : {
                    "soft" : 100
                    "hard" : 23
                    "ok" : 200
                    "manual" : 2
                    "muted" : 1
                }
                ... more sub measurement types ...
            }
        """

        blocks = []
        for model in INSTALLED_SUBMEASUREMENTS:
            # Get the enum type for this sub measurement
            subms_type = SubmeasurementType.from_model(model)
            qs = model.objects.all().values('flag_type').annotate(total_count=Count("flag_type"))
            
            # Create block 
            #   set up initial block data
            block_data = { x.value : 0 for x in SubMeasurement.FlagType}
            #   Store actual data
            for q in qs:
                flag_type = q['flag_type']
                count = q['total_count']

                block_data[flag_type] = count

            blocks.append(Block(subms_type.value, block_data))

        return AggregationResult(BlockType.SUBMEASUREMENT_TYPE, blocks)

    def get_flag_count_per_subms_by_date(self, start_date : datetime, end_date : datetime, subms_type : SubmeasurementType):
        """
            Returns flag count for the specified measurement type divided by day since "start_date" to "end_date"
        """
        query =     f"SELECT date_trunc('day', measurement_start_time) AS block, flag_type, count(flag_type) \
                    FROM {subms_type.table_name} \
                    WHERE measurement_start_time > %s AND measurement_start_time < %s\
                    GROUP BY (block, flag_type) ORDER BY block, flag_type;"

        # Perform query
        with connection.cursor() as cursor:
            cursor.execute(query, [start_date, end_date])
            # Create a dict, so the fields have names too
            col_names = [col[0] for col in cursor.description]
            results = [dict(zip(col_names, row)) for row in cursor.fetchall()]
        
        # Build data for result blocks
        data = {}
        for result in results:
            block_val = result['block']

            # Set up initial values for block data
            if block_val not in data:
                data[block_val] = {x.value : 0 for x in SubMeasurement.FlagType }
            
            # Update block data
            block_data = data[block_val]
            block_data[result['flag_type']] = result['count']
        
        # Build result and return
        blocks = [Block(k, v) for (k,v) in data.items()]
        return AggregationResult(BlockType.DAYS, blocks)


        