import requests
from .auth_client import AuthClient
from django.conf import settings



class InventoryClient:

    @staticmethod
    def reserve_stock(reservations):
        token = AuthClient.get_internal_token()

        

        headers = {
            "Authorization": f"Bearer {token}",
            'Content-Type': 'application/json'
        }

        

        responses = []

        for item in reservations:
            

            response = requests.post(
                f"{settings.INVENTORY_SERVICE_URL}/reserve/",
                json=item,
                headers= headers
            )
            

            if response.status_code != 201:
                raise Exception("Inventory reservation failed")
   
                

            responses.append(response.json())

        return responses
    

    @staticmethod
    def release_stock(reservation):
        token = AuthClient.get_internal_token()

        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(
            f"{settings.INVENTORY_SERVICE_URL}/release/",
            json=reservation,
            headers=headers,
        )

        if response.status_code != 200:
            raise Exception("Inventory release failed")

        return response.json()