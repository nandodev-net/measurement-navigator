from apps.main.measurements                     import models as MeasModels
from apps.main.measurements.submeasurements     import models as SubMModels
from django.core.paginator import Paginator


# dns_ = SubMModels.DNS.objects.all()
# count_dns =  dns_.count()
# dns = Paginator(dns_, 1000)
# i = 1
# for page_idx in range(1, dns.num_pages):
#     for instance in dns.page(page_idx).object_list:
#         print ('duplicating DNS: ', i, 'from', count_dns)

#         if not instance.measurement_start_time:

#             if instance.measurement.raw_measurement.input:
#                 instance.input = instance.measurement.raw_measurement.input

#             if instance.measurement.raw_measurement.measurement_start_time:
#                 instance.measurement_start_time = instance.measurement.raw_measurement.measurement_start_time     

#             if instance.measurement.raw_measurement.probe_asn:
#                 instance.probe_asn = instance.measurement.raw_measurement.probe_asn

#             if instance.measurement.raw_measurement.probe_cc:
#                 instance.probe_cc = instance.measurement.raw_measurement.probe_cc

#             if instance.measurement.anomaly:
#                 instance.anomaly = instance.measurement.anomaly
#             instance.save()

#             i = i+1
#         else:
#             pass


# http_ = SubMModels.HTTP.objects.all()
# count_http =  http_.count()
# http = Paginator(http_, 1000)
# i = 1
# for page_idx in range(1, http.num_pages):
#     for instance in http.page(page_idx).object_list:
#         print ('duplicating HTTP: ', i, 'from', count_http)

#         if not instance.measurement_start_time:
#             if instance.measurement.raw_measurement.input:
#                 instance.input = instance.measurement.raw_measurement.input

#             if instance.measurement.raw_measurement.measurement_start_time:
#                 instance.measurement_start_time = instance.measurement.raw_measurement.measurement_start_time     

#             if instance.measurement.raw_measurement.probe_asn:
#                 instance.probe_asn = instance.measurement.raw_measurement.probe_asn

#             if instance.measurement.raw_measurement.probe_cc:
#                 instance.probe_cc = instance.measurement.raw_measurement.probe_cc

#             if instance.measurement.anomaly:
#                 instance.anomaly = instance.measurement.anomaly
#             instance.save()

#             i = i+1
#         else:
#             pass



tcp_ = SubMModels.TCP.objects.all()
count_tcp =  tcp_.count()
tcp = Paginator(tcp_, 1000)
i = 1
for page_idx in range(1, tcp.num_pages):
    for instance in tcp.page(page_idx).object_list:
        print ('duplicating TCP: ', i, 'from', count_tcp)

        if not instance.time:
            if instance.measurement.raw_measurement.input:
                instance.input = instance.measurement.raw_measurement.input

            if instance.measurement.raw_measurement.measurement_start_time:
                instance.time = instance.measurement.raw_measurement.measurement_start_time     

            if instance.measurement.raw_measurement.probe_asn:
                instance.probe_asn = instance.measurement.raw_measurement.probe_asn

            if instance.measurement.raw_measurement.probe_cc:
                instance.probe_cc = instance.measurement.raw_measurement.probe_cc

            if instance.measurement.anomaly:
                instance.anomaly = instance.measurement.anomaly
            instance.save()
        else:
            pass
        i = i+1



tor_ = SubMModels.TOR.objects.all()
count_tor =  tor_.count()
tor = Paginator(tor_, 1000)

for page_idx in range(1, tor.num_pages):
    i = 1
    for instance in tor.page(page_idx).object_list:
        print ('duplicating TOR: ', i, 'from', count_tor)

        if not instance.time:
            if instance.measurement.raw_measurement.input:
                instance.input = instance.measurement.raw_measurement.input

            if instance.measurement.raw_measurement.measurement_start_time:
                instance.time = instance.measurement.raw_measurement.measurement_start_time     

            if instance.measurement.raw_measurement.probe_asn:
                instance.probe_asn = instance.measurement.raw_measurement.probe_asn

            if instance.measurement.raw_measurement.probe_cc:
                instance.probe_cc = instance.measurement.raw_measurement.probe_cc

            if instance.measurement.anomaly:
                instance.anomaly = instance.measurement.anomaly
            instance.save()
        else:
            pass
        i = i+1