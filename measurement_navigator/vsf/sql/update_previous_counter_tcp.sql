-- This query can update the previous_counter for tcp submeasurements
WITH 
    measurements as (
        SELECT 
            tcp.id as tcp_id, 
            rms.measurement_start_time as start_time,
            f.flag as flag,
            rms.input as input,
            tcp.counted as counted,
            tcp.previous_counter as prev_counter
        FROM submeasurements_tcp tcp    JOIN measurements_measurement ms ON ms.id = tcp.measurement_id
                                        JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id
                                        JOIN flags_flag f ON f.id = tcp.flag_id
        ORDER BY input, start_time, prev_counter, tcp_id
    ),
    ms_to_update as (
        SELECT DISTINCT ms.input 
        FROM measurements ms 
        WHERE NOT ms.counted
    ),
    sq as (
        SELECT 
            ms.tcp_id as id, 
            ms.input  as input, 
            ms.flag   as flag, 
            SUM(CAST(ms.flag<>'ok' AS INT)) OVER (PARTITION BY ms.input ORDER BY ms.start_time, ms.prev_counter, ms.tcp_id) as prev_counter
        FROM measurements ms JOIN ms_to_update on ms_to_update.input = ms.input
    )

UPDATE submeasurements_tcp tcp
    SET 
        previous_counter = sq.prev_counter,
        counted = CAST(1 as BOOLEAN)
    FROM sq
    WHERE tcp.id = sq.id;