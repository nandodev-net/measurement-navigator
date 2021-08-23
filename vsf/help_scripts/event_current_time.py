from apps.main.events.models                import Event


events_qs = Event.objects.all()
event_num = events_qs.count()
i=1

for instance in events_qs:
    print("updating ", i ," from ", event_num, "Events")
    instance.current_start_date = instance.start_date
    instance.current_end_date = instance.end_date
    instance.save()
    i=i+1