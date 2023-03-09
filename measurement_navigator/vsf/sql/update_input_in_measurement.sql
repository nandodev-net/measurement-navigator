-- This SQL query updates the measurement.input fk so that it points to the correct url entry

WITH measurements AS 
    (
        SELECT rms.input as input, ms.input_id as input_id, ms.id as measurement_id FROM 
            measurements_rawmeasurement rms join measurements_measurement ms ON rms.id=ms.raw_measurement_id
    )
UPDATE measurements_measurement ms1
    SET input_id = urls.id

    FROM measurements ms JOIN sites_url urls ON ms.input=urls.url

    WHERE ms1.id=ms.measurement_id;

