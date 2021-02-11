from django.db                      import models
from django.contrib.postgres.fields import JSONField


class SiteCategory(models.Model):

    class CodeType(models.TextChoices):
        """
        	Every kind of possible code value
        """

        ALDR    = 'ALDR'
        REL     = 'REL'
        PORN    = 'PORN'
        PROV    = 'PROV' 
        POLR    = 'POLR' 
        HUMR    = 'HUMR' 
        ENV     = 'ENV' 
        MILX    = 'MILX' 
        HATE    = 'HATE' 
        NEWS    = 'NEWS' 
        XED     = 'XED' 
        PUBH    = 'PUBH' 
        GMB     = 'GMB' 
        ANON    = 'ANON' 
        DATE    = 'DATE' 
        GRP     = 'GRP' 
        LGBT    = 'LGBT' 
        FILE    = 'FILE' 
        HACK    = 'HACK' 
        COMT    = 'COMT' 
        MMED    = 'MMED' 
        HOST    = 'HOST' 
        SRCH    = 'SRCH' 
        GAME    = 'GAME' 
        CULTR   = 'CULTR' 
        ECON    = 'ECON' 
        GOVT    = 'GOVT' 
        COMM    = 'COMM' 
        CTRL    = 'CTRL' 
        IGO     = 'IGO' 
        MISC    = 'MISC'


    class OldCodeType(models.TextChoices):
        """
        	Every kind of possible old code value
        """

        ALDR    = 'ALDR'
        REL     = 'REL'
        PORN    = 'PORN'
        PROV    = 'PROV' 
        POLR    = 'POLR POLT' 
        HUMR    = 'HUMR MINR WOMR MINF' 
        ENV     = 'ENV' 
        MILX    = 'MILX' 
        HATE    = 'HATE' 
        NEWS    = 'FEXP' 
        XED     = 'XED' 
        PUBH    = 'PUBH SELFHARM' 
        GMB     = 'GMB' 
        ANON    = 'ANON' 
        DATE    = 'DATE' 
        GRP     = 'GRP' 
        LGBT    = 'GAYL' 
        FILE    = 'P2P SFTWR WRZ' 
        HACK    = 'HACK' 
        COMT    = 'VOIP EMAIL TRNS MSG' 
        MMED    = 'MMED' 
        HOST    = 'HOST BLGSERV CLOUD' 
        SRCH    = 'SRCH' 
        GAME    = 'GAME' 
        CULTR   = 'HAL' 
        ECON    = 'DEV' 
        GOVT    = 'FREL USMIL' 
        COMM    = 'COMM' 
        CTRL    = 'CACH' 
        IGO     = 'N/A' 
        MISC    = 'MISC KWRD'


    code = models.CharField(
        max_length=20, 
        null=False, 
        choices=CodeType.choices 
    )

    old_code = models.CharField(
        max_length=20, 
        null=False, 
        choices=OldCodeType.choices 
    )

    category_spa = models.TextField()  

    category_eng = models.TextField(
                    null = True,
                    blank = True 
            )  

    description_spa = models.TextField()    

    description_eng = models.TextField(     
                    null = True,
                    blank = True 
            )

    def __str__(self):
        return str(self.code) + " : " + str(self.category_spa)


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

    category = models.ForeignKey(
        SiteCategory,
        null = True,
        blank = True,
        on_delete=models.SET_NULL
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
