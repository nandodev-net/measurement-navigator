from django.db import models
from model_utils.models import TimeStampedModel

from django.core.exceptions import ValidationError

class Config(TimeStampedModel):

    hardflag_timewindow = models.FloatField(
        default=15.5,
        verbose_name = 'Hard Flag Time Window',
    )

    hardflag_openning_treshold = models.IntegerField(
        default=7,
        verbose_name = 'HardFlag Minimum Measurements',
    )

    hardflag_continue_treshold = models.IntegerField(
        default=5,
        verbose_name = 'HardFlag Minimum Measurements',
    )

    hardflag_interval_size = models.IntegerField(
        default=10,
        verbose_name = "How many measurements to check in each iteration of the algorithm"
    )

    def clean(self):
            num_configs = Config.objects.all().count()
            if num_configs > 1:
                raise ValidationError("You can't create more than {} config instance, please edit the last one.".format(num_configs))