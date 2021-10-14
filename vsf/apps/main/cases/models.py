"""
    Note:  there's currently some foreign key fields with on_delete = CASCADE 
    that have to be checked since they doesn't make sense. 
"""
# Django imports
from django.db      import models
from django.db.models.fields import BooleanField
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

    title_eng = models.CharField(
        max_length=100,
        null=True, 
        blank=True
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

    start_date_manual = models.DateTimeField(
        null=True, 
        blank=True,
    )

    start_date_automatic = models.DateTimeField(
        null=True, 
        blank=True
    )

    end_date = models.DateTimeField(
        null=True, 
        blank=True,
        )

    end_date_manual = models.DateTimeField(
        null=True, 
        blank=True,
    )

    end_date_automatic = models.DateTimeField(
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
    
    is_active = models.BooleanField(
        default = False
    )

    manual_is_active = models.BooleanField(
        default = False
    )

    def get_sites(self) -> dict:

        sites = {}
        for e in self.events.all():
            if e.domain.site:
                sites[e.domain.site.name] = e.domain.site.category

        return sites

    def get_asns(self) -> dict:
        asns = {}
        for e in self.events.all():
            if e.domain.site and e.domain.site.name in asns:
                asns[e.domain.site.name].add(e.asn.name)
            else:
                if e.domain.site:
                    asns[e.domain.site.name] = {}
        return asns

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
            return timezone.now() > self.get_end_date()
        else:
            return None

    def get_short_description(self) -> str:
        if len(self.description) < 61:
            return self.description
        else:
            return self.description[:61]

    def get_twitter_keywords(self) -> list:
        keywords = self.twitter_search.split(' ')
        if len(keywords) > 2:
            filtred_keywords = keywords[:2]
            filtred_keywords.append('+' + str(len(keywords[2:])))
            return filtred_keywords
        else:
            return keywords

    def get_start_date_beautify(self) -> str:
        start_date = self.get_start_date()
        if start_date:
            return beautifyDate(start_date)
        else: return None

    def get_end_date_beautify(self) -> str:
        end_date = self.get_end_date()
        if end_date:
            return beautifyDate(end_date)
        else: return None

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

def beautifyDate(_date) -> str:
    months = {'1': 'enero', '2': 'febrero', '3': 'marzo', '4': 'abril',
        '5': 'mayo', '6': 'junio', '7': 'julio', '8': 'agosto', '9': 'septiembre',
        '10': 'octubre', '11': 'noviembre', '12': 'diciembre'
    }
    return months[str(_date.month)] + ' ' + str(_date.day) + ', ' + str(_date.year)