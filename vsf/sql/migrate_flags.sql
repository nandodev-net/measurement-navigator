UPDATE submeasurements_dns m
SET
    flag_type=f.flag,
    event_id=f.event_id,
    confirmed=f.confirmed
FROM
    submeasurements_dns subm JOIN flags_flag f ON subm.flag_id=f.id
WHERE m.id = subm.id;

UPDATE submeasurements_http m
SET
    flag_type=f.flag,
    event_id=f.event_id,
    confirmed=f.confirmed
FROM
    submeasurements_http subm JOIN flags_flag f ON subm.flag_id=f.id
    
WHERE m.id=subm.id;

UPDATE submeasurements_tcp m
SET
    flag_type=f.flag,
    event_id=f.event_id,
    confirmed=f.confirmed
FROM
    submeasurements_tcp subm JOIN flags_flag f ON subm.flag_id=f.id
where m.id=subm.id;