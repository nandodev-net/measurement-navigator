from datetime import date, datetime

import requests
from celery import shared_task

from apps.main.asns.models import ASN
from apps.main.events.models import Event
from apps.main.public_stats.models import *
from apps.main.sites.models import *
from vsf.utils import VSFTask


def generate_public_stats():
    blocked_domains = []
    blocked_sites = []
    domains = Domain.objects.all()
    print("Generando general stats :")
    for domain in domains:
        event = Event.objects.filter(
            domain=domain, it_continues=True, closed=False, confirmed=True
        )
        if len(event) > 0 and domain.domain_name not in blocked_domains:
            blocked_domains.append(domain.domain_name)
        if domain.site and domain.site.name not in blocked_sites:
            blocked_sites.append(domain.site.name)
    GeneralPublicStats.objects.all().delete()
    GeneralPublicStats.objects.create(
        blocked_domains=len(blocked_domains), blocked_sites=len(blocked_sites)
    )

    asns = ASN.objects.all()
    AsnPublicStats.objects.all().delete()
    print("Generando ASN stats :")
    for asn in asns:
        blocked_domains_by_asn = []
        blocked_sites_by_asn = []
        for domain in domains:
            event = Event.objects.filter(
                domain=domain, asn=asn, it_continues=True, closed=False, confirmed=True
            )  # TODO eventypes en filtrado

            if len(event) > 0 and domain.domain_name not in blocked_domains_by_asn:
                blocked_domains_by_asn.append(domain.domain_name)
            if domain.site and domain.site.name not in blocked_sites_by_asn:
                blocked_sites_by_asn.append(domain.site.name)
        AsnPublicStats.objects.create(
            asn=asn,
            blocked_domains_by_asn=len(blocked_domains_by_asn),
            blocked_sites_by_asn=len(blocked_sites_by_asn),
        )

    categories = SiteCategory.objects.all()
    CategoryPublicStats.objects.all().delete()
    print("Generando category stats :")
    for category in categories:
        blocked_sites_by_category = []
        blocked_domains_by_category = []
        for domain in domains:
            event = Event.objects.filter(
                domain=domain, it_continues=True, closed=False, confirmed=True
            )
            if (
                len(event) > 0
                and domain.site
                and domain.site.category == category
                and domain.domain_name not in blocked_domains_by_category
            ):
                blocked_domains_by_category.append(domain.domain_name)
                if domain.site.name not in blocked_sites_by_category:
                    blocked_sites_by_category.append(domain.site.name)
        CategoryPublicStats.objects.create(
            category=category,
            blocked_sites_by_category=len(blocked_sites_by_category),
            blocked_domains_by_category=len(blocked_domains_by_category),
        )


@shared_task(
    time_limit=10800, vsf_name="update_speed_stats", base=VSFTask
)  # Task triggered every 12 hrs
def update_speed_stats():

    # First checking if there are stats saved from January 1st of the current year.
    # If there are no one saved, that means that the speed stats task has never triggered

    current_year = str(date.today().year)
    january_first = "01/01/" + current_year
    january_first_object = datetime.strptime(january_first, "%d/%m/%Y")

    first_day_of_the_year_speed_stat = SpeedInternet.objects.filter(
        day=january_first_object
    ).first()

    data = requests.get(
        "https://statistics.measurementlab.net/v0/SA/VE/"
        + current_year
        + "/histogram_daily_stats.json"
    )
    data = data.json()

    asns = ASN.objects.all()

    if first_day_of_the_year_speed_stat:
        # In the other case, we only saved or update the last day.

        element = data[-1]

        speed_internet = SpeedInternet.objects.filter(
            day=datetime.strptime(element["date"], "%Y-%m-%d")
        ).first()
        if speed_internet:
            speed_internet.download_average = float(element["download_AVG"])
            speed_internet.upload_average = float(element["upload_AVG"])
            speed_internet.save()
            print("----- Speed of the last data was saved successfully.")
        else:
            SpeedInternet.objects.create(
                day=datetime.strptime(element["date"], "%Y-%m-%d"),
                download_average=float(element["download_AVG"]),
                upload_average=float(element["upload_AVG"]),
            )
            print("----- Speed of the last data was updated successfully.")

        for asn in asns:
            try:

                print(
                    "https://statistics.measurementlab.net/v0/SA/VE/asn/"
                    + asn.asn[2:]
                    + "/"
                    + current_year
                    + "/histogram_daily_stats.json"
                )
                data_asn = requests.get(
                    "https://statistics.measurementlab.net/v0/SA/VE/asn/"
                    + asn.asn[2:]
                    + "/"
                    + current_year
                    + "/histogram_daily_stats.json"
                )
                data_asn = data_asn.json()
                element = data_asn[-1]

                speed_internet_by_asn = SpeedInternetByISP.objects.filter(
                    day=datetime.strptime(element["date"], "%Y-%m-%d"), asn=asn
                ).first()

                if speed_internet_by_asn:
                    speed_internet_by_asn.download_average = float(
                        element["download_AVG"]
                    )
                    speed_internet_by_asn.upload_average = float(element["upload_AVG"])
                    speed_internet_by_asn.save()
                    print(
                        "----- Last Speed by ASN data from asn "
                        + asn.asn
                        + " was updated successfully."
                    )
                else:
                    SpeedInternetByISP.objects.create(
                        day=datetime.strptime(element["date"], "%Y-%m-%d"),
                        download_average=float(element["download_AVG"]),
                        upload_average=float(element["upload_AVG"]),
                        asn=asn,
                    )
                    print(
                        "----- Last Speed by ASN data from asn "
                        + asn.asn
                        + " was created successfully."
                    )
            except:
                print("----- No ASN " + asn.asn + " founded in MLab Database.")

    else:
        for element in data:

            same_day = SpeedInternet.objects.filter(
                day=datetime.strptime(element["date"], "%Y-%m-%d")
            ).first()
            if same_day:
                same_day.download_average = float(element["download_AVG"])
                same_day.upload_average = float(element["upload_AVG"])
                same_day.save()
            else:
                SpeedInternet.objects.create(
                    day=datetime.strptime(element["date"], "%Y-%m-%d"),
                    download_average=float(element["download_AVG"]),
                    upload_average=float(element["upload_AVG"]),
                )

        print("----- Speed general data was charged successfully.")

        for asn in asns:
            try:
                data_asn = requests.get(
                    "https://statistics.measurementlab.net/v0/SA/VE/asn/"
                    + asn.asn[2:]
                    + "/"
                    + current_year
                    + "/histogram_daily_stats.json"
                )
                data_asn = data_asn.json()

                for element in data_asn:

                    same_day = SpeedInternetByISP.objects.filter(
                        day=datetime.strptime(element["date"], "%Y-%m-%d"), asn=asn
                    ).first()

                    if same_day:
                        same_day.download_average = float(element["download_AVG"])
                        same_day.upload_average = float(element["upload_AVG"])
                        same_day.save()
                    else:
                        SpeedInternetByISP.objects.create(
                            day=datetime.strptime(element["date"], "%Y-%m-%d"),
                            download_average=float(element["download_AVG"]),
                            upload_average=float(element["upload_AVG"]),
                            asn=asn,
                        )
                print(
                    "----- Speed by ASN data from asn "
                    + asn.asn
                    + " was charge successfully."
                )
            except:
                print("----- No ASN " + asn.asn + " founded in MLab Database.")
