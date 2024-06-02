"""
This app controls the data coming from ooni api through the pipeline,
in order to show the realtime view with the preview data for the data
that will be available for further analysis in the following days

"""

from django.apps import AppConfig


class FpTablesConfig(AppConfig):
    name = "apps.main.ooni_fp.fp_tables"
