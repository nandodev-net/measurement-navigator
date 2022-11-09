"""
This app represents the 'Site object', which is a way to 
control which urls belongs to a corresponding site 
(And other information). For example:
    - myblockedsite.com
    - myblockedsite.es
    They both correspond to the same site 'myblockedsite' even though 
    they have different urls. 

In order to set the site corresponding to a new url, the user must explictly 
add this url to the right site.
"""

from django.apps import AppConfig


class SitesConfig(AppConfig):
    name = 'apps.main.sites'
