from apps.main.measurements.models import Measurement as ms, RawMeasurement as rm
from apps.main.asns.models import ASN


universe = ms.objects.all()
iguales = 0
diferentes = 0

iguales2 = 0
diferentes2 = 0

for meas in universe:
    if meas.raw_measurement.probe_asn == meas.asn.asn:
        iguales = iguales+1
    else:
        diferentes = diferentes+1
    print('-------')
    print(' ',meas.raw_measurement.probe_asn ,' - ',meas.asn.asn)
    print('iguales: ', iguales)
    print('diferentes: ', diferentes)

    if  meas.domain.domain_name in meas.raw_measurement.input:
        iguales2 = iguales2+1
    else:
        diferentes2 = diferentes2+1    

    print(' ',meas.raw_measurement.input ,' - ',meas.domain.domain_name)
    print('iguales: ', iguales2)
    print('diferentes: ', diferentes2)   