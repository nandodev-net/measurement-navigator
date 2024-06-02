from requests import Response
from rest_framework.views import APIView

from . import utils


class FastPathIngestView(APIView):
    """
    This view will receive a post request containing the CC (contry code),
    since (start date), until (end date), and if the data is valid, it will perform
    a get request to the ooni api to store data that matches the provided data and then store it
    in the data base. Since the data format that comes from the fast path is not
    uniform and well-known, we can't use a serializer. We have to perform data validation
    by hand.

    The expected dates should be in the following format:
        YYYY-mm-dd
    """

    # i don't know if this should be in settings @TODO
    """
        The url where de data will be asked to the ooni fast path
    """
    ooni_url = "https://api.ooni.io/api/v1/measurements"

    def post(self, request, since, until, only_fastpath: bool = False, format=None):
        # try:
        (status, measurements) = utils.request_fp_data(
            since, until, from_fastpath=only_fastpath
        )
        # except:
        #    return Response([], status=HTTP_400_BAD_REQUEST)

        return Response(measurements, status=status)
