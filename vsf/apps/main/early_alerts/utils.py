# This file contains this app basic logic that should be called by views 
# and periodic tasks

# Django imports
from django.core.mail import send_mail

# Third party imports
from datetime import timedelta, datetime
from typing   import List
# Local imports
from .                      import ooni_data_processor as ooni_dp
from .models                import Emails, Input,EarlyAlertConfig
from vsf.utils              import Colors as c  
from vsf.settings.settings  import EMAIL_HOST_USER


def update_last_anomaly_rate_on_config():
    """
        Like update_last_anomaly_rate, but searching its params from 
        the database 
    """
    config = EarlyAlertConfig.objects.filter(is_current_config=True).first()

    # Provide default config values is not config is provided
    if not config:
        delta : timedelta = timedelta(days=1)
        alarming_rate : float = 0.1
    else:
        delta : timedelta = timedelta(
                                days=config.days_before_now, 
                                hours=config.hours_before_now, 
                                minutes=config.minutes_before_now
                            )
        alarming_rate : float = config.alarmin_rate_delta
    
    update_last_anomaly_rate(delta, alarming_rate)


def update_last_anomaly_rate(delta : timedelta = timedelta(days=1), alarming_rate : float = 0.1):
    """
    Summary:
        Update the 'last_anomaly_rate' field in the database, 
        by computing the new last_anomaly_rate and storing the older one.
        If the difference between the currently stored and the recently computed
        is too high, raise an email alert
    Params:
        delta : deltatime = how much time before now to take in consideration
                            when updating the previous counter. For example, "take measurements 
                            since 1 day before until now, get the anomaly rate and compare it
                            to the currently stored"
        alarming_rate : float = a float between -1 and 1 that represents an alarming delta 
                                between de last anomaly rate and the cunrrent one. For example,
                                current_anomaly_rate - last_anomaly_rate == 0.1 implies that
                                the anomaly_rate increased by 10% since the last time it was measured
    """

    assert -1 <= alarming_rate <= 1, "alarming_rate should be in the range [-1,1]"

    inputs = Input.objects.all()

    # Compute until and since
    until = datetime.now()
    since = until - delta

    # Create a new procesor storing data since 'since'
    processor = ooni_dp.DataProcessor(since, until, delta)

    # Request data for our current measurement set, don't bring details per step
    # as we don't need them. Use a generator since we don't need to store the entire list
    processor.get(( (i.input, i.asn) for i in inputs), True)

    for input in inputs:
        #  Get Results for this measurement
        result   : ooni_dp.AnalysisResult = processor.get_results(input.input,input.asn)

        # If could not retrieve something, just keep going
        if result is None: continue

        new_rate : float = result.anomaly_rate()

        # update anomaly_rate
        input.previous_anomaly_rate = input.last_anomaly_rate
        input.last_anomaly_rate = new_rate

        # Check if we should report an alert
        delta : float = new_rate - input.previous_anomaly_rate
        if input.last_anomaly_rate  - input.previous_anomaly_rate > alarming_rate:
            alert(input, delta)

        # Save the new data
        input.save()


def alert(input : Input, delta : float):
    """
    Summary:
        Trigger an alert when the provided input instance 
        has an alarming delta
    Params:
        input : Input = Input instance that triggered the alert
        delta : float = anomaly_rate delta that was bigger than our treshold
    """
    emails = Emails.objects.all()
    config = EarlyAlertConfig.get_config()

    if config is None: return # can't send emails if i don't have a sender email

    now = datetime.now()

    subject = f"[ALERT] {input.input} for asn {input.asn}"
    message = f"{input.input} for asn {input.asn} has an alarming variation in its changing rate of {delta} at {now}"
    to = [i.email for i in emails]
    send_mail(subject, message, EMAIL_HOST_USER, to, False)
    print(c.red(f"[ALERT] {input.input} for asn {input.asn} has an alarming changing rate of {delta}"))


def load_inputs_from_file(file : str):
    """
    Summary:
        Try to open this file and load a set of inputs. The file should 
        have the following format:
        url1 asn1
        url2 asn2
        ...
        urln asnn
    """

    content : List[str] = []
    with open(file) as f:
        content = f.readlines()

    content = map(lambda c: c.strip().split(),content)
    for line in content:
        url, asn = line
        asn = asn.upper()
        if not asn.startswith("AS"): asn = "AS" + asn
        Input.add_input(asn, url)