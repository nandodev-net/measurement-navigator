UPDATE submeasurements_dns 
SET
    flag_type=f.flag,
    event_id=f.event_id,
    confirmed=f.confirmed
FROM
    submeasurements_dns subm JOIN flags_flag f ON subm.flag_id=f.id;

UPDATE submeasurements_http 
SET
    flag_type=f.flag,
    event_id=f.event_id,
    confirmed=f.confirmed
FROM
    submeasurements_http subm JOIN flags_flag f ON subm.flag_id=f.id;

UPDATE submeasurements_tcp 
SET
    flag_type=f.flag,
    event_id=f.event_id,
    confirmed=f.confirmed
FROM
    submeasurements_tcp subm JOIN flags_flag f ON subm.flag_id=f.id;