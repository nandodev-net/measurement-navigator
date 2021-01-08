from apps.main.measurements.models import Measurement
from apps.main.sites.models        import Domain
from vsf.utils                     import get_domain


qs = Measurement.objects.all().select_related('raw_measurement')
updated = []
for q in qs:
    if q.raw_measurement.input is None:
        continue
    domain, _ = Domain.objects.get_or_create(domain_name = get_domain(q.raw_measurement.input), defaults={'site':None})
    q.domain = domain
    q.save()
