"""
    Helper script to load default asns into the database; i don't think this should be done
    like this, so we should discuss it later. @TODO
"""
from apps.main.asns.models import ASN
import json 
asns_file = "init_data/fixture_asns.json"

with open(asns_file) as json_file:
    data = json.load(json_file)
    for elem in data:
        name = elem['fields']['name']
        
        (asn, created) = ASN.objects.get_or_create(asn=elem['fields']['asn'], defaults={'name' : name})

        if asn.name != name:
            asn.name = name
            asn.save()

