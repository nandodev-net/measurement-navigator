/* List DNS submeasurements:
    ordered by:
        domain, asn, start_time, previous counter, id
    showing:
        id, domain id, asn, flag type, previous counter, date
*/

WITH 
    measurements as (           -- This subquery will build a table with all the data we need, nothing magic here, just more 
        SELECT                  -- joins than i would like and some sorting
            subm.id as subm_id, 
            rms.measurement_start_time as start_time,
            subm.flag_type as flag,
            ms.domain_id as domain,
            rms.probe_asn as asn,
            event_id,
            subm.flagged as flagged,
            subm.counted as counted,
            subm.previous_counter as prev_counter
        FROM submeasurements_dns subm  JOIN measurements_measurement ms ON ms.id = subm.measurement_id
                                        JOIN measurements_rawmeasurement rms ON rms.id = ms.raw_measurement_id
        ORDER BY domain, asn, start_time, prev_counter, subm_id
    )
select subm_id, domain, asn, start_time, flag, event_id, prev_counter, flagged, counted from measurements;