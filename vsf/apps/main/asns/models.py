from django.db import models
from django.contrib.postgres.fields import JSONField


# Create your models here.

class ASN(models.Model):
    """
        This model represents an ASN that may have more than 
        one Measurement related  
    """
    asn = models.CharField(            # Autonomous System Number
                null=False, 
                max_length=40
            )

    name = models.CharField(            # Name of the ISP
                unique=True,
                null=True, 
                blank=True,
                max_length=100
            )

    # This json contains a list with the references to the reports related to this url
    # The format for this json should be { "reports" : [measurement.tid] }
    reports = JSONField(
                unique=True,
                null=True, 
                blank=True
            )     
    # This json contains a list with the references to the reports related to this url
    # The format for this json should be { "references" : [FastPath.tid] }
    fp_references = JSONField(
                unique=True,
                null=True, 
                blank=True
            )
