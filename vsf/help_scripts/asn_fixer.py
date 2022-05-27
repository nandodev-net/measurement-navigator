from apps.main.measurements.models import Measurement as ms, RawMeasurement as rm
from apps.main.asns.models import ASN


universe = ms.objects.all()
i=1
total=len(universe)

for meas in universe:
    print(i,' of ', total)
    if meas.raw_measurement.probe_asn:
        if meas.raw_measurement.probe_asn == meas.asn.asn:
            pass
        else:
            asn_ = meas.raw_measurement.probe_asn
            print(asn_,'  -  ', meas.asn)
            asn,_ = ASN.objects.get_or_create(asn=asn_)
            meas.asn = asn
            meas.save()
            print(asn_,'  -  ', meas.asn)
            print('----------------------------')
        i=i+1


