from apps.main.measurements.models import Measurement
from apps.main.sites.models        import Domain
from apps.main.asns.models         import ASN
from vsf.utils                     import get_domain


qs = Measurement.objects.all().select_related('raw_measurement').exclude(raw_measurement__input=None).filter(domain=None)
updated = []
for q in qs:
    
    domain, _ = Domain.objects.get_or_create(domain_name = get_domain(q.raw_measurement.input), defaults={'site':None})
    q.domain = domain
    q.save()
    del q
