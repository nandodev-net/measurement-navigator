from apps.main.measurements.models import Measurement
from apps.main.sites.models        import Domain
from apps.main.asns.models         import ASN
from vsf.utils                     import get_domain


qs = Measurement.objects.all().select_related('raw_measurement').exclude(raw_measurement__probe_asn=None).filter(asn=None)
to_update = []
count = 0
for q in qs.iterator():
    asn, _ = ASN.objects.get_or_create(asn = q.raw_measurement.probe_asn, defaults={'name':None})
    q.asn = asn
    to_update.append(q)
    if len(to_update) == 2000:
        count += len(to_update)
        print(f"{count} measurements saved so far")
        Measurement.objects.bulk_update(to_update, ['asn'])
        to_update = []

if len(to_update) != 0:
    Measurement.objects.bulk_update(to_update, ['asn'])


        
