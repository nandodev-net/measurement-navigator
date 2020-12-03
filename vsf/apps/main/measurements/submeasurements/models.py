
# Django imports
from django.db                      import models
from django.contrib.postgres.fields import JSONField

# Local imports
from apps.main.measurements.models                       import Measurement
from apps.main.measurements.flags.models                 import Flag
# Create your models here.
class SubMeasurement(models.Model):
    """
    Base class for a sub measurement. Depending on its type, 
    each measurement may have multiple sub measurements. This 
    is the base class for such objects
    """
    measurement = models.ForeignKey(
                                    to=Measurement,
                                    on_delete=models.CASCADE)
    flag = models.ForeignKey(to=Flag, null=True, on_delete=models.SET_NULL)

    # The following fields are required for the hard flag logic:
    # The 'previous_counter' field stores an integer 'N' such that 
    # N = the ammount of measurements such that each measurement m holds:
    #   * m is soft flagged
    #   * m.start_time < self.start_time
    #   * m.measurement.raw_measurement.input == self.measurement.raw_measurement.input
    previous_counter = models.IntegerField(default=0)

    def save(   self, 
                force_insert=False, 
                force_update=False, 
                using=None,
                update_fields=None):
        # We import this here so we can avoid circular imports
        from .utils import check_submeasurement   
        
        should_flag = check_submeasurement(self)
        flag_type = Flag.FlagType.SOFT if should_flag else Flag.FlagType.OK
        try:
            self.flag = Flag.objects.create(flag=flag_type)
        except:
            pass

        return super().save(force_insert, force_update, using, update_fields)

    class Meta:
        abstract = True # When abstract is True, django wont make a table for this model

class DNSJsonFields(models.Model):
    """
        Test model to check performance penalty for json data storage
    """
    control_resolver_answers = JSONField(null=True)
    answers = JSONField(null=True)

class DNS(SubMeasurement):
    """
    Model for DNS submeasurement, which can be found, for example,
    in web_connectivity or DNS tests
    """
    control_resolver_failure = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )
    control_resolver_hostname = models.GenericIPAddressField(
        null=True, blank=True)  # servidor DNS de control

    failure = models.CharField(max_length=50, null=True, blank=True)
    resolver_hostname = models.GenericIPAddressField(
        null=True, blank=True)  # servidor DNS que se esta evaluando, (target)

    inconsistent = models.NullBooleanField()
    dns_consistency  = models.CharField(max_length=50, null=True, blank=True)
    hostname = models.CharField(max_length=100, null=True, blank=True) # añadido por Luis, Andrés debe revisar esto
    jsons = models.ForeignKey(to=DNSJsonFields, null=True, on_delete=models.SET_NULL)



class HTTP(SubMeasurement):
    """
        Model for HTTP measurement, part of web connectivity measurements
    """
    status_code_match = models.BooleanField(default=False)
    headers_match = models.BooleanField(default=False)
    body_length_match = models.BooleanField(default=False)
    body_proportion = models.FloatField()

class TCP(SubMeasurement):
    """
        Model for TCP submeasurement, part of web connectivity tests
    """
    status_blocked = models.BooleanField(default=False)
    status_failure = models.TextField(null=True)
    status_success = models.BooleanField(default=True)
    ip             = models.CharField(max_length=50, null=True)