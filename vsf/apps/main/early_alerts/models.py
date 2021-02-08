# Django imports
from django.db import models

# Third party imports
from typing import List

# Create your models here.
class Input(models.Model):
    """
        An input is an entry formed by an url and an ASN,
        then we feed such pair into the ooni api to get agregated data.
        There's a lot of ways to add input to this table, so we won't related directly 
        to our other apps. Instead, we will provide an interface to add elements.
        Try not to make it so big so we don't overload the ooni api with a lot of requests.
    """
    input = models.URLField(
                            verbose_name='input url', 
                            editable=True
                        )
    asn   = models.CharField(
                            verbose_name='internet provider ASN',
                            editable=True,
                            max_length=20              
                        )

    @staticmethod
    def clear_table():
        """
            Remove all inputs from the table
        """
        Input.objects.delete()

    @staticmethod
    def add_inputs(inputs):
        """
            Add a list of pairs (url, asn) to the table
        """
        input_set = set(inputs)
        already_existing = set(
                        (i.input, i.asn) for i in Input.objects.filter(
                            input__in = [url for (url,_) in inputs], 
                            asn__in   = [ asn for (_,asn) in inputs]
                        )
                    )
        input_set -= already_existing
        input_objects = ( Input(input=url, asn=asn) for (url, asn) in input_set )
        Input.objects.bulk_create(input_objects)

    @staticmethod
    def add_input(asn : str, input : str):
        """
            Add a single input to the input list. If it already exists, it's not going to be added
        """
        Input.objects.get_or_create(asn=asn, input=input)

    @staticmethod
    def remove_input(asn : str, input : str):
        Input.objects.filter(asn=asn, input=input).delete()