"""
    Note:  there's currently some foreign key fields with on_delete = CASCADE 
    that have to be checked since they doesn't make sense. 
"""
# Django imports
from django.db      import models
from django.urls    import reverse
from django.conf    import settings
from datetime       import date as d

from django.db.models.deletion import SET_NULL

# Project imports
from apps.main.events.models import Event
from apps.main.sites.models import Domain 


class Category(models.Model):
    name = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=50)
 
    def get_absolute_url(self):
        return reverse('category-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Case(models.Model):

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

    start_date = models.DateField(
        null=True, 
        blank=True,
    )

    end_date = models.DateField(
        null=True, 
        blank=True,
        )

    category = models.ForeignKey(   
        to=Category,                          
        related_name="cases",
        on_delete=models.DO_NOTHING,
        )

    draft = models.BooleanField(
        default=True,
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

                            
    def __str__(self):
        return self.title


class Update(models.Model):
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
    created = models.DateField(default=d.today)

    def __str__(self):
        return self.title
