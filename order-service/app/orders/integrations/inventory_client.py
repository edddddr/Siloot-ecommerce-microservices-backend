import requests
import os

INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL")


class InventoryClient:

    @staticmethod
    def reserve_stock(reservations):

        responses = []

        for item in reservations:

            response = requests.post(
                f"{INVENTORY_SERVICE_URL}/reserve",
                json=item
            )

            if response.status_code != 200:
                raise Exception("Inventory reservation failed")

            responses.append(response.json())

        return responses
    

    @staticmethod
    def release_stock(reservation):

        response = requests.post(
            f"{INVENTORY_SERVICE_URL}/release",
            json=reservation
        )

        if response.status_code != 200:
            raise Exception("Inventory release failed")

        return response.json()