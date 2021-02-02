from django.db import models

# Create your models here.
# Django imports
from django.db                      import models
from django.utils                   import timezone

# Third party imports
import uuid

# Application imports
from apps.main.events.models import Event

class Flag(models.Model):
    """
        A flag entry identifies a measurement that has some kind of 
        issue. A measurement with no flag is a regular measurement,
        with soft flag, the measurement has some kind of anomaly, and
        a hard flag means that the measurement might be part of a blocking
        event. Muted is a measurement to ignore.
    """

    class FlagType(models.TextChoices):
        """
        	Every kind of possible flag value
        """
        OK 		     = "ok"     # The measurement has no problems
        SOFT 	     = "soft"   # The measurement has some problem
        HARD         = "hard"   # this measurement is grouped with other measurements as they have a common problem
        MUTED		 = "muted"  # ignore this measurement
        MANUAL       = "manual" # The measurement has set as it has a possible problem

    
    uuid = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False, 
        db_index=True
    )
    
    # Flag type
    flag = models.CharField(
        max_length=10, 
        null=False, 
        choices=FlagType.choices, 
        default=FlagType.OK
    )

    event = models.ForeignKey(
        to=Event, 
        null=True,
        blank=True, 
        on_delete=models.SET_NULL,
        related_name = 'flags'
    )

    confirmed = models.BooleanField(
        default = False,
        verbose_name = 'confirmed?'
    )
 
    # Date when this flag was created
    creation_date = models.DateTimeField(
        editable=False, 
        auto_now_add=True
        )

    # Update date:
    update_date = models.DateTimeField(
        auto_now=True
        )

    def __str__(self):
        return str(self.flag) + " : " + str(self.creation_date)

    