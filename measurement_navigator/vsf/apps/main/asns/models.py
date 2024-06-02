from django.db import models
from model_utils.models import TimeStampedModel

# Create your models here.


class ASN(TimeStampedModel):
    """
    This model represents an ASN that may have more than
    one Measurement related
    """

    asn = models.CharField(null=False, max_length=40)  # Autonomous System Number

    name = models.CharField(  # Name of the ISP
        unique=True, null=True, blank=True, max_length=100
    )

    def __str__(self):
        return self.asn
