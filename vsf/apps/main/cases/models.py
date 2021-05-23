"""
    Note:  there's currently some foreign key fields with on_delete = CASCADE 
    that have to be checked since they doesn't make sense. 
"""
# Django imports
from django.db      import models
from model_utils.models import TimeStampedModel
from django.urls    import reverse
from django.conf    import settings
from datetime       import date as d, datetime
from django.utils   import timezone

from django.db.models.deletion import SET_NULL

# Project imports
from apps.main.events.models import Event
from apps.main.sites.models import Domain 


class Category(TimeStampedModel):
    name = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=50)
 
    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Case(TimeStampedModel):

    TYPE_CATEGORIES = (
        ('bloqueo', 'Bloqueo'),
        ('desconexion', 'Desconexion'),
        ('relentizacion', 'Relentizacion de servicio en Linea'),
        ('conexion', 'Conexion inusualmente lenta'),
        ('intercepcion', 'Intercepcion de trafico'),
        ('falla', 'Falla Importante'),
        ('dos', 'DoS')
    )

    title = models.CharField(
        max_length=100
        )

    description = models.TextField(
        null=True, 
        blank=True,
        verbose_name = 'description_spa'
    )

    description_eng = models.TextField(
        null=True, 
        blank=True,
        verbose_name = 'description_eng'
    )

    case_type = models.CharField(
        choices=TYPE_CATEGORIES, 
        max_length=50,
        default = 'bloqueo',
        )

    start_date = models.DateTimeField(
        null=True, 
        blank=True,
    )

    end_date = models.DateTimeField(
        null=True, 
        blank=True,
        )

    category = models.ForeignKey(   
        to=Category,                          
        related_name="cases",
        on_delete=models.DO_NOTHING,
        )

    published = models.BooleanField(
        default=False,
        )

    events = models.ManyToManyField(
        Event,
        blank=True,
        related_name="cases",
        )

    twitter_search = models.CharField(
        max_length=400, 
        null=True, 
        blank=True,
        )

    def get_start_date(self) -> datetime:
        """
            Get start date depending if it's set up to auto or 
            manual. If start_date is null, then return minimum start_date from every related event.
            Otherwise, return start_date

            It may return None when there's no cases and manual date is set to None
        """

        if self.start_date:
            return self.start_date

        # if no events, return None.
        if (events := self.events.all()):
            return min(e.get_end_date() for e in events)
        else:
            return None 

    def get_end_date(self) -> datetime:
        """
            Get end date depending if it's set up to auto or 
            manual. If end_date is null, then return maximum end_date from every related event.
            Otherwise, return start_date.

            It may return None when there's no events and manual date is set to None
        """

        if self.end_date:
            return self.end_date

        # if no events, return None.
        if (events := self.events.all()):
            return max(e.get_end_date() for e in events)
        else:
            return None

    def is_case_expired(self) -> bool:
        if self.get_end_date():
            return timezone.now() < self.get_end_date()
        else:
            return None

    def get_short_description(self) -> str:
        if len(self.description) < 61:
            return self.description
        else:
            return self.description[:61]

    def get_twitter_keywords(self) -> list:
        return self.twitter_search.split(' ')

    def __str__(self):
        return self.title


class Update(TimeStampedModel):
    TYPE = (
        ('info', 'Info'),
        ('grave', 'Grave'),
        ('positivo', 'Positivo')
    )

    date = models.DateField()
    title = models.CharField(max_length=100)
    text = models.TextField()
    category = models.CharField(choices=TYPE, max_length=20)
    case = models.ForeignKey(   to=Case, 
                                on_delete=models.CASCADE, #FOR DEBUGGING, CHECK LATER @TODO
                                related_name="updates")
    created_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, #FOR DEBUGGING, CHECK LATER @TODO
        related_name='updates',
        null=True, blank=True
    )

    def __str__(self):
        return self.title
