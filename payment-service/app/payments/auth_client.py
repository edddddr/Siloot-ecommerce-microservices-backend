import requests
from django.conf import settings


class AuthClient:

    @staticmethod
    def get_internal_token():

        url = f"{settings.AUTH_SERVICE_URL}/auth/internal/token/"

        payload = {
            "service_name": settings.SERVICE_NAME,
            "service_secret": settings.SERVICE_SECRET
        }

        response = requests.post(url, json=payload)

        response.raise_for_status()

        return response.json()["access_token"]