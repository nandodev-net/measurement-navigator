from django.db import models
from model_utils.models import TimeStampedModel

from apps.main.asns.models import ASN
from apps.main.sites.models import SiteCategory


class GeneralPublicStats(TimeStampedModel):

    blocked_domains = models.IntegerField(
        default=0,
    )

    blocked_sites = models.IntegerField(
        default=0,
    )


class AsnPublicStats(TimeStampedModel):

    blocked_sites_by_asn = models.IntegerField(
        default=0,
    )

    blocked_domains_by_asn = models.IntegerField(
        default=0,
    )

    asn = models.OneToOneField(
        ASN,
        on_delete=models.DO_NOTHING,
        primary_key=True,
    )


class CategoryPublicStats(TimeStampedModel):

    blocked_sites_by_category = models.IntegerField(
        default=0,
    )

    blocked_domains_by_category = models.IntegerField(
        default=0,
    )

    category = models.OneToOneField(
        SiteCategory,
        on_delete=models.DO_NOTHING,
        primary_key=True,
    )


class SpeedInternet(TimeStampedModel):

    day = models.DateField(primary_key=True)
    download_average = models.DecimalField(max_digits=4, decimal_places=1)
    upload_average = models.DecimalField(max_digits=4, decimal_places=1)


class SpeedInternetByISP(TimeStampedModel):

    day = models.DateField()

    download_average = models.DecimalField(max_digits=4, decimal_places=1)
    upload_average = models.DecimalField(max_digits=4, decimal_places=1)
    asn = models.ForeignKey(
        ASN,
        null=False,
        on_delete=models.DO_NOTHING,
    )
