update submeasurements_dns m
set 
    counted=cast(0 as BOOLEAN),
    flagged=cast(0 as BOOLEAN),
    previous_counter=0;
    
update submeasurements_tcp m
set 
    counted=cast(0 as BOOLEAN),
    flagged=cast(0 as BOOLEAN),
    previous_counter=0;
update submeasurements_http m
set 
    counted=cast(0 as BOOLEAN),
    flagged=cast(0 as BOOLEAN),
    previous_counter=0;

update submeasurements_tor m
set 
    counted=cast(0 as BOOLEAN),
    flagged=cast(0 as BOOLEAN),
    previous_counter=0;

update submeasurements_dns 
set 
    flag_type='soft',
    event_id=NULL
WHERE flag_type='hard';

update submeasurements_tcp 
set 
    flag_type='soft',
    event_id=NULL
WHERE flag_type='hard';

update submeasurements_http 
set 
    flag_type='soft',
    event_id=NULL
WHERE flag_type='hard';

update submeasurements_tor
set 
    flag_type='soft',
    event_id=NULL
WHERE flag_type='hard';


DELETE FROM cases_case_events;

DELETE FROM events_event;