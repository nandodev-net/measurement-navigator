from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db.models.deletion import SET_NULL
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from model_utils.models import TimeStampedModel

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=50, 
        unique = True,
    )

    first_name = models.CharField(
        max_length=50, 
        blank=True, 
        null=True
        )

    last_name = models.CharField(
        max_length=50, 
        blank=True, 
        null=True
        )

    email = models.EmailField(_('email address'), 
        unique=True
        )

    is_admin = models.BooleanField(
        default=False
        )

    is_analist = models.BooleanField(
        default=False
        )

    is_editor = models.BooleanField(
        default=False
        )

    is_staff = models.BooleanField(
        default=False
        )

    is_active = models.BooleanField(
        default=True
        )

    date_joined = models.DateTimeField(
        default=timezone.now
        )
    

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email',]

    objects = CustomUserManager()

    def __str__(self):
        return self.email