from apps.main.measurements.models import Measurement
from apps.main.sites.models        import Domain
from apps.main.asns.models         import ASN
from vsf.utils                     import get_domain


qs = Measurement.objects.all().select_related('raw_measurement').exclude(raw_measurement__input=None).filter(domain=None)
to_update = []
count = 0
for q in qs.iterator():
    domain, _ = Domain.objects.get_or_create(domain_name = get_domain(q.raw_measurement.input), defaults={'site':None})
    q.domain = domain
    to_update.append(q)
    if to_update == 10000:
        count += len(to_update)
        print(f"Updated {count} measurements so far")
        Measurement.objects.bulk_update(to_update, ['domain'])
        to_update = []

if len(to_update) != 0: Measurement.objects.bulk_update(to_update, ['domain'])

