import requests
import os

PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL")


class PaymentClient:

    @staticmethod
    def start_payment(payload):

        response = requests.post(
            PAYMENT_SERVICE_URL,
            json=payload
        )

        if response.status_code not in [200, 201]:
            raise Exception("Payment initiation failed")

        return response.json()