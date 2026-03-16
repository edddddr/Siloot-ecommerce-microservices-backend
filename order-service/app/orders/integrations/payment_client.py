import requests
from django.conf import settings 
from .auth_client import AuthClient




class PaymentClient:

    @staticmethod
    def start_payment(payload):
        token = AuthClient.get_internal_token()

        headers = {
            "Authorization": f"Bearer {token}",
            'Content-Type': 'application/json'
        }

        

        response = requests.post(
            f"{settings.PAYMENT_SERVICE_URL}/",
            json=payload,
            headers=headers
        )

        print("\n",response.json())

        if response.status_code not in [200, 201]:
            raise Exception("Payment initiation failed")

        return response.json()