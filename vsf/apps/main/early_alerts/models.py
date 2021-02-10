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
    input = models.TextField(
                            verbose_name='input url', 
                            editable=True,
                        )
    asn   = models.CharField(
                            verbose_name='internet provider ASN',
                            editable=True,
                            max_length=30              
                        )

    # anomaly rate for the previous time it was checked (time before the last)
    last_anomaly_rate = models.FloatField(default=0)

    # anomaly rate for the last time it was checked
    previous_anomaly_rate = models.FloatField(default=0)

    # When this model was added
    added  = models.DateTimeField(auto_now_add=True)
    
    # When was updated for the last time
    updated = models.DateTimeField(auto_now=True)

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

class EarlyAlertConfig(models.Model):
    """
        Config parameters to take in consideration when computing 
        database updating logic
    """
    # how many days to take in cosideration when requesting for 
    # new measurements
    days_before_now = models.IntegerField(default=0)
    # how many hours to take in cosideration when requesting for 
    # new measurements
    hours_before_now = models.IntegerField(default=1)
    # how many minutes to take in cosideration when requesting for 
    # new measurements
    minutes_before_now = models.IntegerField(default=0)

    # alarming anomaly rate change:
    alarming_rate_delta = 0.1

    # If this row is te actual configuration to use
    is_current_config = models.BooleanField(default=False)

    @staticmethod
    def get_config():
        """
        Summary:
            get the current config. It may return none if no config is active
        """
        return EarlyAlertConfig.objects.filter(is_current_config=True).first()

class Emails(models.Model):
    """
        Emails to be notified when an event is triggered
    """
    email = models.EmailField(null=False, verbose_name="Email to be notified", unique=True)
