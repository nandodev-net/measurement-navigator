from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = [env.str('VSF_PRODUCTION_HOST1'), env.str('VSF_PRODUCTION_HOST2'), env.str('VSF_PRODUCTION_HOST3')]
