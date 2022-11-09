from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = env.str('DJANGO_ALLOWED_HOSTS').split()
CSRF_TRUSTED_ORIGINS = origins.split(" ") if (origins := env("CSRF_TRUSTED_ORIGINS", default="")) else [] # type: ignore
BASE_URL = BASE_DIR