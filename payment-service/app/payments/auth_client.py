import requests
from django.conf import settings


class AuthClient:

    @staticmethod
    def get_internal_token():

        url = f"{settings.AUTH_SERVICE_URL}/internal/token/"
        headers = {
            "X-Internal-Secret": settings.INTERNAL_SERVICE_SECRET,
            'Content-Type': 'application/json'
            }

        payload = {
            "service_name": settings.SERVICE_NAME,
            
        }

        response = requests.post(url, json=payload, headers=headers)

        response.raise_for_status()

        return response.json()["access"]