import os

import requests
from dotenv import load_dotenv


class GisHelper:
    def __init__(self):
        self.mapbox_key = os.getenv('MAPBOX_KEY_GEOCODER')

    def reverse_geocode(self, point):
        """
        Geocode latitude and longitude into a human-readable address using Mapbox API.
        """

        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{point[0]},{point[1]}.json"

        params = {
            'access_token': self.mapbox_key,
            'limit': 1
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if data['features']:
                return data['features'][0]['place_name']

        return f"Punto GPS {point[0]}, {point[1]}"
