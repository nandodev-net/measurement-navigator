from apps.main.measurements                     import models as MeasModels
from apps.main.measurements.submeasurements     import models as SubMModels
from django.db import connection
from dateutil import rrule

with connection.cursor() as c:
    c.execute("SELECT pg_size_pretty( pg_database_size('vsf_db') );")
    print('Tam DB total: ',c.fetchall(), '\n\n')

##############################################################################################

with connection.cursor() as c:
    c.execute("SELECT pg_size_pretty(pg_total_relation_size('measurements_measurement'))")
    print('Tam total Measurements: ',c.fetchall())

meas_ = MeasModels.Measurement.objects.all()
count_meas =  meas_.count()
first_meas_date = MeasModels.Measurement.objects.earliest('created').created
last_meas_date = MeasModels.Measurement.objects.latest('created').created

print('Num total MEAS: ', count_meas)
print('First MEAS: ', first_meas_date)
print('Last MEAS: ', last_meas_date)
months = rrule.rrule(rrule.MONTHLY, dtstart=first_meas_date, until=last_meas_date).count()
print("MEAS months: ", months,'\n\n')

#######################################################################
with connection.cursor() as c:
    c.execute("SELECT pg_size_pretty(pg_total_relation_size('measurements_rawmeasurement'))")
    print('Tam total RAWMeasurements: ',c.fetchall())

meas_ = MeasModels.RawMeasurement.objects.all()
count_meas =  meas_.count()
first_meas_date = MeasModels.RawMeasurement.objects.earliest('created').created
last_meas_date = MeasModels.RawMeasurement.objects.latest('created').created

print('Num total RAWMEAS: ', count_meas)
print('First RAWMEAS: ', first_meas_date)
print('Last RAWMEAS: ', last_meas_date)
months = rrule.rrule(rrule.MONTHLY, dtstart=first_meas_date, until=last_meas_date).count()
print("RAWMEAS months: ", months,'\n\n')

###################################################################################################

with connection.cursor() as c:
    c.execute("SELECT pg_size_pretty(pg_total_relation_size('submeasurements_dns'))")
    print('Tam total DNS: ',c.fetchall())

dns_ = SubMModels.DNS.objects.all()
count_dns =  dns_.count()
first_dns_date = SubMModels.DNS.objects.earliest('created').created
last_dns_date = SubMModels.DNS.objects.latest('created').created
print('Num total DNS: ', count_dns)
print('First DNS Date: ', first_dns_date)
print('Last DNS Date: ', last_dns_date)
months = rrule.rrule(rrule.MONTHLY, dtstart=first_dns_date, until=last_dns_date).count()
print("DNS months: ", months,'\n\n')


###################################################################################################

with connection.cursor() as c:
    c.execute("SELECT pg_size_pretty(pg_total_relation_size('submeasurements_http'))")
    print('Tam total HTTP: ',c.fetchall())

http_ = SubMModels.HTTP.objects.all()
count_http =  http_.count()
first_http_date = SubMModels.HTTP.objects.earliest('created').created
last_http_date = SubMModels.HTTP.objects.latest('created').created
print('Num total HTTP: ', count_http)
print('First HTTP Date: ', first_http_date)
print('Last HTTP Date: ', last_http_date)
months = rrule.rrule(rrule.MONTHLY, dtstart=first_http_date, until=last_http_date).count()
print("HTTP months: ", months,'\n\n')

##################################################################################################

with connection.cursor() as c:
    c.execute("SELECT pg_size_pretty(pg_total_relation_size('submeasurements_tcp'))")
    print('Tam total TCP: ',c.fetchall())

tcp_ = SubMModels.TCP.objects.all()
count_tcp =  tcp_.count()
first_tcp_date = SubMModels.TCP.objects.earliest('created').created
last_tcp_date = SubMModels.TCP.objects.latest('created').created
print('Num total TCP: ', count_tcp)
print('First TCP Date: ', first_tcp_date)
print('Last TCP Date: ', last_tcp_date)
months = rrule.rrule(rrule.MONTHLY, dtstart=first_tcp_date, until=last_tcp_date).count()
print("TCP months: ", months,'\n\n')


