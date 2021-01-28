from django.db                      import models
from django.contrib.postgres.fields import JSONField

# Create your models here.
class Site(models.Model):
    """
        This model represents a Site that may have more than 
        one URL related  
    """
    
    name = models.CharField(            # Name of the site
                unique=True,
                null=False, 
                max_length=40
            )
    description_spa = models.TextField()    # A simple spanish description for the site 

    description_eng = models.TextField(     # A simple English description for this site (optional)
                    null = True,
                    blank = True 
            )

class URL(models.Model):
    """
        This model represents a simple URL that may (or not) be related
        to some site. Every url starts without a site until the user sets its  
        corresponding site. Every url stores its reports in a single json 
        so it's easier to get every report for each url.
    """

    url = models.URLField(
                unique=True,
                null=False,
                db_index=True
            )
            
    #if a site is deleted, set this field to null since a lot of reports would be lost
    site = models.ForeignKey(
                to=Site, 
                null=True,
                on_delete=models.SET_NULL 
            )

    # This json contains a list with the references to the reports related to this url
    # The format for this json should be { "reports" : [measurement.tid] }
    reports = JSONField(default=dict)       
    # This json contains a list with the references to the reports related to this url
    # The format for this json should be { "references" : [FastPath.tid] }
    fp_references = JSONField(default=dict)

class Domain(models.Model):
    """
    A domain is used to group multiple measurements to its corresponding 
    domain.

    For example, if we got the following url:
        https://www.google.com/some_search

        It's domain_name value will be:
            www.google.com
    """
    domain_name = models.TextField(unique=True)
    site = models.ForeignKey(
        to=Site,
        null=True,
        on_delete=models.SET_NULL
    )

    # We use this field to check whether there are new measurements 
    # with this ASN, so we can now which measurements take when
    # counting or updating flags
    recently_updated = models.BooleanField(default=True)