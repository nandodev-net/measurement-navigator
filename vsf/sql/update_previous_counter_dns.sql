-- This query can update the previous_counter for dns submeasurements
EXPLAIN analyze WITH sq as (
    SELECT 
            dns.id as dns_id, 
            sum(CAST(f.flag='soft' AS INT)) OVER (PARTITION BY rms.input ORDER BY rms.measurement_start_time, dns.id ASC) as previous
    FROM
        submeasurements_dns dns JOIN measurements_measurement ms ON ms.id = dns.measurement_id
                                JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id
                                JOIN flags_flag f ON f.id = dns.flag_id
    )
UPDATE submeasurements_dns dns
    SET 
        previous_counter = sq.previous
    FROM sq
    WHERE dns.id = sq.dns_id;