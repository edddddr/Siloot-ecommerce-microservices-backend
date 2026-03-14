import uuid
import random

from django.conf import settings
from django.db import transaction

from .models import Payment, PaymentTransaction, PaymentStatus


class PaymentService:
    @staticmethod
    def create_payment(order_id, amount, currency="USD"):

        payment = Payment.objects.create(
            order_id=order_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING
        )

        return payment


    @staticmethod
    def simulate_gateway():

        # 80% success rate
        return random.random() < 0.8



    @staticmethod
    @transaction.atomic
    def process_payment(payment: Payment):

        payment.status = PaymentStatus.PROCESSING
        payment.save(update_fields=["status"])

        result = PaymentService.simulate_gateway()

        if result:
            payment.status = PaymentStatus.SUCCEEDED
        else:
            payment.status = PaymentStatus.FAILED

        payment.save(update_fields=["status"])

        PaymentService.create_transaction(payment)

        return payment

    
    @staticmethod
    def create_transaction(payment):

        PaymentTransaction.objects.create(
            payment=payment,
            provider="mock_gateway",
            transaction_id=str(uuid.uuid4()),
            status=payment.status,
            response_payload={
                "message": "Simulated payment gateway"
            }
        )

        PaymentService.notify_order_service(payment)

        return payment



    @staticmethod
    def notify_order_service(payment):

        if payment.status == PaymentStatus.SUCCEEDED:
            endpoint = "/orders/payment-success/"
        else:
            endpoint = "/orders/payment-failed/"

        # This will be implemented in Step 7
        print(f"Notify Order Service: {endpoint}")
