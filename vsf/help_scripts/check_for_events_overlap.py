"""Use this 
script to check for events overlapping. This is a serious error
that we should be able to catch, but doing so by hand is kinda hard, 
so use this script to check for overlaps
"""

from typing import Dict, List, Tuple
from datetime import datetime

from apps.main.events.models import Event
from vsf.utils import Colors as c

# Dict from (type, asn, domain) -> [(start_time, end_time, id)]
event_groups : Dict[Tuple[str, str, str], List[Tuple[datetime, datetime, int]]] = {}

qs = Event.objects.all().iterator()
for event in qs:
    ev : Event = event

    event_type = ev.issue_type
    event_asn = ev.asn.asn
    domain = ev.domain.domain_name
    ev_start_date = ev.start_date
    ev_end_date = ev.end_date
    ev_id = ev.id

    key = (event_type, event_asn, domain)

    # Create default list
    if key not in event_groups:
        event_groups[key] = []

    # Get list of pairs of start and end date
    event_list = event_groups[key]

    for (start_date, end_date, id) in event_list:
        if  (start_date <= ev_start_date <= end_date) or \
            (start_date <= ev_end_date <= end_date) or \
            (start_date <= ev_start_date <= ev_end_date <= end_date):
            print(c.red(f"[WARNING] Found overlapping events with ids {ev_id}, {id} with type: {event_type}, asn: {event_asn} and domain: {domain}"))

            print(c.red(f"First event ({ev_id}): "))
            print(c.red(f"\t- start_date: {ev_start_date}"))
            print(c.red(f"\t- end_date: {ev_end_date}"))

            print(c.red(f"Second event ({id}): "))
            print(c.red(f"\t- start_date: {start_date}"))
            print(c.red(f"\t- end_date: {end_date}"))
        event_list.append((ev_start_date, ev_end_date, ev_id))
    
