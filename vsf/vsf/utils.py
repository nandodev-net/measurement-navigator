"""
    Utility functions to use throughout the project.
"""
# Django imports
from django.db.models       import OuterRef, Subquery
from django.db.models.query import QuerySet

# Third party imports
import bisect

# Local imports
from apps.main.measurements.models  import Measurement, RawMeasurement
from apps.main.sites.models         import Site, URL

def MeasurementXRawMeasurementXSite() -> QuerySet:
    """
        Join measurement with raw measurement and its corresponding site.
        The site member it's available with the 'site' name.

        example:
        qs = MeasurementXRawMeasurementXSite()
        qs[0].site == foreign key to a site if it exist, None otherwise
    """

    urls = URL.objects.all().select_related('site').filter(url=OuterRef('raw_measurement__input'))
    qs   = Measurement.objects.all()\
                .select_related('raw_measurement')\
                .annotate(
                        site=Subquery(urls.values('site')),
                        site_name=Subquery(urls.values('site__name'))
                    )

    return qs


# -- Some algorithm help ----

