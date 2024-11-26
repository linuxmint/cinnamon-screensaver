import json
from types import SimpleNamespace

import requests

from util.location import LocationProvider, LocationData

URL = "https://get.geojs.io/v1/ip/geo.json"

class GeoJSLocationProvider(LocationProvider):
    """
    LocationProvider implementation for geojs.io
    """

    def __init__(self):
        pass

    @staticmethod
    def GetLocation() -> LocationData:
        response = requests.get(URL)

        data = json.loads(response.text, object_hook=lambda d: SimpleNamespace(**d))

        return LocationData(float(data.latitude), float(data.longitude), data.city, data.country, data.timezone, data.city)