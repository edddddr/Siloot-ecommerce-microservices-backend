# import uuid
# import random
# import time

# from django.conf import settings
# from django.db import transaction

# from .models import Payment, PaymentTransaction, PaymentStatus
# from .auth_client import AuthClient                
# from .serializers import OrderResultSerializer

# import requests
# from django.conf import settings


# class PaymentService:
#     @staticmethod
#     def create_payment(order_id, amount, currency="USD"):

#         payment = Payment.objects.create(
#             order_id=order_id,
#             amount=amount,
#             currency=currency,
#             status=PaymentStatus.PENDING
#         )

#         print("Payment was created")

#         return payment


#     @staticmethod
#     def simulate_gateway():

#         print("simulated was called")
#         # 80% success rate
#         # return random.random() < 0.8
#         return True



#     @staticmethod
#     @transaction.atomic
#     def process_payment(payment: Payment):

#         payment.status = PaymentStatus.PROCESSING
#         payment.save(update_fields=["status"])

#         result = PaymentService.simulate_gateway()

#         print("Payment was proccessed")

#         if result:
#             payment.status = PaymentStatus.SUCCEEDED
#         else:
#             payment.status = PaymentStatus.FAILED

#         payment.save(update_fields=["status"])

#         PaymentService.create_transaction(payment)

#         return payment

    
#     @staticmethod
#     def create_transaction(payment):

#         print("transactions was regitred")

#         PaymentTransaction.objects.create(
#             payment=payment,
#             provider="mock_gateway",
#             transaction_id=str(uuid.uuid4()),
#             status=payment.status,
#             response_payload={
#                 "message": "Simulated payment gateway"
#             }
#         )

#         PaymentService.notify_order_service(payment)

#         return payment



#     @staticmethod
#     def notify_order_service(payment):

#         token = AuthClient.get_internal_token()

#         print("internal token : ", token)
        

#         headers = {
#             "Authorization": f"Bearer {token}"
#         }


#         serializer = OrderResultSerializer(data={"order_id": payment.order_id})
#         serializer.is_valid()
#         order_id = serializer.data["order_id"]

#         payload = {
#             "order_id": order_id
#         }

            

#         if payment.status == PaymentStatus.SUCCEEDED:
#             url = f"{settings.ORDER_SERVICE_URL}/payment-success/"
#             print(payload, "SUCCEEDED")
#         else:
#             url = f"{settings.ORDER_SERVICE_URL}/payment-failed/"

#         retries = 3
#         delay = 2

#         for attempt in range(retries):
#             try:
#                 response = requests.post(url, json=payload, headers=headers, timeout=5)

#                 if response.status_code == 200:
#                     print("Order Service notified successfully")
#                     return True

#             except Exception as e:
#                 print("Failed to notify Order Service:", str(e))

#             time.sleep(delay)        


#         print("Failed to notify Order Service after retries")
#         return False        


from django.conf import settings
import requests

CHAPA_SECRET = settings.CHAPA_SECRET

print("CHAPA_SECRET -----------------------: ", CHAPA_SECRET)

class ChapaService:

    @staticmethod
    def initialize_payment(data):
        url = "https://api.chapa.co/v1/transaction/initialize"

        payload = {
            "amount": "6119.97",
            "currency": "ETB",
            "email": "test@gmail.com", # Hardcode a simple address here
            "first_name": "John",
            "last_name": "Doe",
            "tx_ref": data["tx_ref"],
            "callback_url": "http://localhost:8000/api/v1/payments/webhook/",
            "return_url": f"http://localhost:8000/payment-result?order_id={data['order_id']}"
        }

        headers = {
            "Authorization": f"Bearer {CHAPA_SECRET}"
        }

        res = requests.post(url, json=payload, headers=headers)
        
        response_data = res.json()

        if response_data.get("status") != "success":
            print("Chapa Error:", response_data)
            return None

        data = response_data.get("data")

        if not data:
            print("Chapa returned no data:", response_data)
            return None

        return data.get("checkout_url")