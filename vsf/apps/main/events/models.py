# WARNING: There's a lot of fields that require to be checked at some point,
# they're marked with a @TODO, please fix this configuration before launching 
# the production build

# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from datetime import datetime
from django.db.models.base import Model  

from django.db.models.deletion import SET_NULL

from apps.main.sites.models     import Domain 
from apps.main.asns.models      import ASN

class Event(models.Model):

    class IssueType(models.TextChoices):
        """
        	Every type of issue
        """
        TCP     =   'tcp'
        DNS     =   'dns'
        HTTP    =   'http'
        NDT     =   'ndt'
        NONE    =   'none'

    # Issue name
    identification = models.CharField(
        max_length=200
    )

    # Confirmed by an human
    confirmed = models.BooleanField(
        default = False,
        verbose_name = 'confirmed?'
    )

    # First Measurement date
    start_date = models.DateTimeField(
        auto_now_add=True, 
        blank=True
    )

    # Last measurement date
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

    # Type of issue
    issue_type = models.CharField(
        max_length=10, 
        null=False, 
        choices=IssueType.choices, 
        default = IssueType.NONE
    )

    it_continues = models.BooleanField(
        default = True,
    )

    domain  = models.ForeignKey(
                            to=Domain,
                            null=True,
                            on_delete=SET_NULL
                            ) 

    asn = models.ForeignKey(
                            to=ASN,
                            null=True,
                            on_delete=SET_NULL
                            ) 

    # If true, then this event won't register new measurements
    closed = models.BooleanField(default=False) 

    # Set up by user, with higher priority than automated start date
    manual_start_date = models.DateTimeField(
        null = True,
        default = None,
        blank= True
    )

    # Set up by user, with higher priority than automated start date
    manual_end_date = models.DateTimeField(
        null = True,
        default = None,
        blank= True
    )

    def generate_title(self) -> str:
        """
            This function will return a string that should be used as auto-title
            for this event
        """
        min_date = self.start_date
        asn = self.asn
        type = self.issue_type
        identification = f"{type} ISSUE FROM {min_date.strftime('%Y-%m-%d %H:%M:%S')}\ FOR ISP {asn.asn if asn else 'UNKNOWN_ASN'} ({asn.name if asn else 'UNKNOWN_ASN'})"
        return identification

    def get_start_date(self) -> datetime:
        """
            This function returns initial date for this event. If 
            manual start date is null, return actual start date. Otherwise, 
            return manual start date
        """

        return self.manual_start_date or self.start_date

    def get_end_date(self) -> datetime:
        """
            This function returns initial date for this event. If 
            manual start date is null, return actual start date. Otherwise, 
            return manual start date
        """

        return self.manual_end_date or self.end_date

    def __str__(self):
        return u"%s" % self.identification
