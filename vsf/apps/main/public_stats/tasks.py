from apps.main.events.models import Event
from apps.main.sites.models import *
from apps.main.asns.models import ASN
from apps.main.public_stats.models import *


def generate_public_stats():
    blocked_domains=[]
    blocked_sites=[]
    domains = Domain.objects.all()
    print('Generando general stats :')
    for domain in domains:
        event = Event.objects.filter(domain=domain, it_continues=True, closed=False, confirmed=True)
        if len(event)>0 and domain.domain_name not in blocked_domains:
            blocked_domains.append(domain.domain_name)
        if domain.site and domain.site.name not in blocked_sites:
            blocked_sites.append(domain.site.name)
    GeneralPublicStats.objects.all().delete()
    GeneralPublicStats.objects.create(blocked_domains=len(blocked_domains), blocked_sites=len(blocked_sites))
    
    asns = ASN.objects.all()
    AsnPublicStats.objects.all().delete()
    print('Generando ASN stats :')
    for asn in asns:
        blocked_domains_by_asn=[]
        blocked_sites_by_asn=[]
        for domain in domains:
            event = Event.objects.filter(domain=domain, asn=asn, it_continues=True, closed=False, confirmed=True)
            if len(event)>0 and domain.domain_name not in blocked_domains_by_asn:
                blocked_domains_by_asn.append(domain.domain_name)
            if domain.site and domain.site.name not in blocked_sites_by_asn:
                blocked_sites_by_asn.append(domain.site.name)
        AsnPublicStats.objects.create(asn=asn, blocked_domains_by_asn=len(blocked_domains_by_asn), blocked_sites_by_asn=len(blocked_sites_by_asn))
    
    categories = SiteCategory.objects.all()
    CategoryPublicStats.objects.all().delete()
    print('Generando category stats :')
    for category in categories:
        blocked_sites_by_category=[]
        blocked_domains_by_category=[]
        for domain in domains:
            event = Event.objects.filter(domain=domain, it_continues=True, closed=False, confirmed=True)
            if len(event)>0 and domain.site and domain.site.category==category and domain.domain_name not in blocked_domains_by_category:
                blocked_domains_by_category.append(domain.domain_name)
                if domain.site.name not in blocked_sites_by_category:
                    blocked_sites_by_category.append(domain.site.name)
        CategoryPublicStats.objects.create(category=category, blocked_sites_by_category=len(blocked_sites_by_category), blocked_domains_by_category=len(blocked_domains_by_category))
