from distutils.command.config import config
from django.db import models
from model_utils.models import TimeStampedModel

from django.core.exceptions import ValidationError



class SingletonModel(models.Model):
    """Singleton Django Model"""

    class Meta:
        abstract = True

   

    @classmethod
    def load(cls):
        """
        Load object from the database. Failing that, create a new empty
        (default) instance of the object and return it (without saving it
        to the database).
        """

        

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

    @classmethod
    def get(cls):
        """Get a model instance. Create one if no instance exists.
        """
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()

    def save(self, *args, **kwargs):
        """
        Save object to the database. Removes all other entries if there
        are any.
        """
        self.__class__.objects.exclude(id=self.id).delete()
        super(SingletonModel, self).save(*args, **kwargs)

    def clean(self):
            num_configs = Config.objects.all().count()
            if num_configs > 1:
                raise ValidationError("You can't create more than {} config instance, please edit the last one.".format(num_configs))