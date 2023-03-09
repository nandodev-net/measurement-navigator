# Script to clean cache after reboot
from django.core.cache import cache

cache.clear()