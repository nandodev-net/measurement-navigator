"""
    Helper script to load default site categories into the database; i don't think this should be done
    like this, so we should discuss it later. @TODO
"""
from apps.main.sites.models import SiteCategory
import json 
asns_file = "init_data/fixture_site_categories.json"

with open(asns_file) as json_file:
    data = json.load(json_file)
    for elem in data:
        fields = elem['fields']
        
        SiteCategory.objects.get_or_create(
                code            = fields['code'], 
                old_code        = fields['old_code'], 
                category_spa    = fields['category_spa'], 
                category_eng    = fields['category_eng'], 
                description_spa = fields['description_spa'], 
                description_eng = fields['description_eng'], 

                defaults={})

        

