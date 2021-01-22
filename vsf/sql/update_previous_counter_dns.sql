-- This query can update the previous_counter for dns submeasurements
WITH 
    measurements as (
        SELECT 
            dns.id as dns_id, 
            rms.measurement_start_time as start_time,
            f.flag as flag,
            rms.input as input,
            dns.counted as counted,
            dns.previous_counter as prev_counter
        FROM submeasurements_dns dns    JOIN measurements_measurement ms ON ms.id = dns.measurement_id
                                        JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id
                                        JOIN flags_flag f ON f.id = dns.flag_id
        ORDER BY input, start_time, prev_counter, dns_id
    ),
    ms_to_update as (
        SELECT DISTINCT ms.input 
        FROM measurements ms 
        WHERE NOT ms.counted
    ),
    sq as (
        SELECT 
            ms.dns_id as id, 
            ms.input  as input, 
            ms.flag   as flag, 
            SUM(CAST(ms.flag<>'ok' AS INT)) OVER (PARTITION BY ms.input ORDER BY ms.start_time, ms.prev_counter, ms.dns_id) as prev_counter
        FROM measurements ms JOIN ms_to_update on ms_to_update.input = ms.input
    )
-- SELECT * FROM sq;

UPDATE submeasurements_dns dns
    SET 
        previous_counter = sq.prev_counter,
        counted = CAST(1 as BOOLEAN)
    FROM sq
    WHERE dns.id = sq.id;