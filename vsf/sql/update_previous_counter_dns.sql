-- This query will update the previous_counter for dns submeasurements
WITH 
    measurements as (           -- This subquery will build a table with all the data we need, nothing magic here, just more 
        SELECT                  -- joins than i would like and some sorting
            dns.id as dns_id, 
            rms.measurement_start_time as start_time,
            f.flag as flag,
            ms.domain_id as domain,
            asn.id       as asn,
            dns.counted as counted,
            dns.previous_counter as prev_counter
        FROM submeasurements_dns dns    JOIN measurements_measurement ms ON ms.id = dns.measurement_id
                                        JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id
                                        JOIN flags_flag f ON f.id = dns.flag_id
                                        JOIN asns_asn asn ON ms.asn_id = asn.id
                                        JOIN sites_domain doms ON ms.domain_id = doms.id
        WHERE doms.recently_updated AND asn.recently_updated
        ORDER BY domain, asn, start_time, prev_counter, dns_id
    ),
    sq as (
        /*
            Here's the hard thing. First we join measurements with the input list (which is as described above),
            so we can filter out measurmeent partitions that does not require a previous_counter update.

            Then, we sum up flag!=ok for every measurement in each partition, so that the accumulate value
            at each row corresponds to the number of issued measurements in the previous rows + if the current 
            row has an issued measurement.
            for example:
            input | flag | previous
            --------------------
            a     |  ok  | later_previous + flag!=ok = 0
            a     | soft | later_previous + flag!=ok = 1
            a     | soft | later_previous + flag!=ok = 2
            a     | soft | later_previous + flag!=ok = 3
            b     | soft | later_previous + flag!=ok = 1
            b     |  ok  | later_previous + flag!=ok = 1
        */
        SELECT 
            ms.dns_id   as id, 
            ms.domain   as domain, 
            ms.flag     as flag,
            ms.asn      as asn, 
            -- ms.asn      as asn, --debug
            SUM(CAST(ms.flag<>'ok' AS INT)) OVER (PARTITION BY ms.domain, ms.asn ORDER BY ms.start_time, ms.prev_counter, ms.dns_id) as prev_counter
        FROM measurements ms
    ),
    update_asns as (
        UPDATE asns_asn asns
        SET
            recently_updated = CAST(0 as BOOLEAN)
        FROM (select distinct asn from measurements) measurements 
        WHERE 
            asns.id=measurements.asn AND NOT recently_updated
    ),
    updated_domains as (
        UPDATE sites_domain doms
        SET 
            recently_updated = CAST(0 AS BOOLEAN)
        FROM (select distinct domain from measurements) measurements
        WHERE
            doms.id = measurements.domain AND NOT recently_updated
    )
UPDATE submeasurements_dns dns
    SET 
    -- Simple update, set the new prev_counter value to its new value
    -- and the counted field to true
    previous_counter = sq.prev_counter
    FROM sq
    WHERE dns.id = sq.id AND (dns.previous_counter<>sq.prev_counter)