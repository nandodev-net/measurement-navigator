-- This query can update the previous_counter for tcp submeasurements
EXPLAIN analyze WITH sq as (
    SELECT 
            tcp.id as tcp_id, 
            sum(CAST(f.flag='soft' AS INT)) OVER (PARTITION BY rms.input ORDER BY rms.measurement_start_time, tcp.id ASC) as previous
    FROM
        submeasurements_tcp tcp JOIN measurements_measurement ms ON ms.id = tcp.measurement_id
                                JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id
                                JOIN flags_flag f ON f.id = tcp.flag_id
    )
UPDATE submeasurements_tcp tcp
    SET 
        previous_counter = sq.previous
    FROM sq
    WHERE tcp.id = sq.tcp_id;