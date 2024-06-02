# Django imports

# Third party imports
import json
from uuid import UUID

# Local imoports
from . import models


# DEPRECATED
def update_urls_fp_refs():
    """
    every url will have a list of reports in the fast path
    table pointing to it, this function updates such list to include
    new fast path entries
    """

    # There's no a fast way to make a query like this, so we use raw queries.
    urlsXfp_refs = models.URL.objects.raw(
        "SELECT id, tid FROM fp_tables_fastpath JOIN sites_url ON (url = input)"
    )

    cache: dict = {}
    for res in urlsXfp_refs:
        if cache.get(res.id) == None:
            cache[res.id] = models.URL.objects.get(id=res.id)

        url = cache[res.id]

        if url.fp_references == {}:
            url.fp_references["references"] = []

        references = url.fp_references["references"]

        if res.tid not in references:
            references.append(res.tid)

    for _, value in cache.items():
        value.save()


# DEPRECATED
def update_urls_reports():
    """
    every url will have measurements related, and such measurements are
    stored the 'reports' jsonfield. This function updates the list within
    that jsonfield
    """

    # There's no a fast way to make a query like this, so we use raw queries.
    urlsXmeasurements = models.URL.objects.raw(
        "SELECT sites_url.id, measurements_measurement.id as mid FROM measurements_measurement JOIN sites_url ON (url = input)"
    )

    cache: dict = {}
    for res in urlsXmeasurements:
        if cache.get(res.id) == None:
            cache[res.id] = models.URL.objects.get(id=res.id)

        url = cache[res.id]

        if url.reports == {}:
            url.reports["reports"] = []

        reports = url.reports["reports"]

        if res.mid not in reports:
            # We remove first and last char since the json encouder adds
            # string literals inside the string, i don't know exactly why or where
            uuid = json.dumps(res.mid, cls=UUIDEncoder)
            uuid = uuid[1 : len(uuid) - 1]
            reports.append(uuid)

    for _, value in cache.items():
        value.save()


# This class is required so we can serialize a uuid
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return obj.hex
        return json.JSONEncoder.default(self, obj)
