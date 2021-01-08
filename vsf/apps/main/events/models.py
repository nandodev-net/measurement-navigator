# WARNING: There's a lot of fields that require to be checked at some point,
# they're marked with a @TODO, please fix this configuration before launching 
# the production build

# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from datetime import datetime  

class Event(models.Model):

    class IssueType(models.TextChoices):
        """
        	Every kind of possible issue
        """
        TCP     =   'tcp'
        DNS     =   'dns'
        HTTP    =   'http'
        NDT     =   'ndt'
        NONE    =   'none'

    identification = models.CharField(
        max_length=200
    )

    confirmed = models.BooleanField(
        default = False,
        verbose_name = 'confirmed?'
    )

    start_date = models.DateTimeField(
        auto_now_add=True, 
        blank=True
    )

    end_date = models.DateTimeField(
        null=True, 
        blank=True
    )

    public_evidence = models.TextField(
        null=True, 
        blank=True
    )

    private_evidence = models.TextField(
        null=True, 
        blank=True
    )

    issue_type = models.CharField(
        max_length=10, 
        null=False, 
        choices=IssueType.choices, 
        default = IssueType.NONE
    )


    def __str__(self):
        return u"%s" % self.identification
