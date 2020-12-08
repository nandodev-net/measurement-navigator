from django.db import models
from django.core.exceptions import ValidationError

class Config(models.Model):

    hardflag_timewindow = models.IntegerField(
        default=1,
        verbose_name = 'HardFlag Time Window',
    )

    hardflag_minmeasurements = models.IntegerField(
        default=3,
        verbose_name = 'HardFlag Minimum Measurements',

    )

    def clean(self):
            numPosts = Config.objects.all().count()
            if numPosts >= 1:
                raise ValidationError("You can't create more than {} config instance, please edit the last one.".format(numPosts))