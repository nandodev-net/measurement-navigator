from apps.main.measurements                     import models as MeasModels
from apps.main.measurements.submeasurements     import models as SubMModels

dns = SubMModels.DNS.objects.all()
count_dns =  dns.count()
i = 1

for instance in dns:
    print ('duplicating DNS: ', i, 'from', count_dns)

    if instance.measurement.raw_measurement.input:
        instance.input = instance.measurement.raw_measurement.input

    if instance.measurement.raw_measurement.measurement_start_time:
        instance.measurement_start_time = instance.measurement.raw_measurement.measurement_start_time     

    if instance.measurement.raw_measurement.probe_asn:
        instance.probe_asn = instance.measurement.raw_measurement.probe_asn

    if instance.measurement.raw_measurement.probe_cc:
        instance.probe_cc = instance.measurement.raw_measurement.probe_cc

    if instance.measurement.anomaly:
        instance.anomaly = instance.measurement.anomaly
    instance.save()

    i = i+1


http = SubMModels.HTTP.objects.all()
count_http =  http.count()
i = 1

for instance in http:
    print ('duplicating HTTP: ', i, 'from', count_http)

    if instance.measurement.raw_measurement.input:
        instance.input = instance.measurement.raw_measurement.input

    if instance.measurement.raw_measurement.measurement_start_time:
        instance.measurement_start_time = instance.measurement.raw_measurement.measurement_start_time     

    if instance.measurement.raw_measurement.probe_asn:
        instance.probe_asn = instance.measurement.raw_measurement.probe_asn

    if instance.measurement.raw_measurement.probe_cc:
        instance.probe_cc = instance.measurement.raw_measurement.probe_cc

    if instance.measurement.anomaly:
        instance.anomaly = instance.measurement.anomaly
    instance.save()

    i = i+1



tcp = SubMModels.TCP.objects.all()
count_tcp =  tcp.count()
i = 1

for instance in tcp:
    print ('duplicating TCP: ', i, 'from', count_tcp)

    if instance.measurement.raw_measurement.input:
        instance.input = instance.measurement.raw_measurement.input

    if instance.measurement.raw_measurement.measurement_start_time:
        instance.measurement_start_time = instance.measurement.raw_measurement.measurement_start_time     

    if instance.measurement.raw_measurement.probe_asn:
        instance.probe_asn = instance.measurement.raw_measurement.probe_asn

    if instance.measurement.raw_measurement.probe_cc:
        instance.probe_cc = instance.measurement.raw_measurement.probe_cc

    if instance.measurement.anomaly:
        instance.anomaly = instance.measurement.anomaly
    instance.save()

    i = i+1


tor = SubMModels.TOR.objects.all()
count_tor =  tor.count()
i = 1

for instance in tor:
    print ('duplicating TOR: ', i, 'from', count_tor)

    if instance.measurement.raw_measurement.input:
        instance.input = instance.measurement.raw_measurement.input

    if instance.measurement.raw_measurement.measurement_start_time:
        instance.measurement_start_time = instance.measurement.raw_measurement.measurement_start_time     

    if instance.measurement.raw_measurement.probe_asn:
        instance.probe_asn = instance.measurement.raw_measurement.probe_asn

    if instance.measurement.raw_measurement.probe_cc:
        instance.probe_cc = instance.measurement.raw_measurement.probe_cc

    if instance.measurement.anomaly:
        instance.anomaly = instance.measurement.anomaly
    instance.save()

    i = i+1