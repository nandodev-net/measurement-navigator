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
    description = models.TextField()    # A simple description for the site

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