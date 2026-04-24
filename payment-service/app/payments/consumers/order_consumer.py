import json
from payments.common.messaging.rabbitmq import EventConsumer
from payments.models import Payment
from payments.services import ChapaService
import uuid


class OrderCreatedConsumer(EventConsumer):
    def __init__(self):
        super().__init__(
            queue_name="payment_order_created",
            routing_key="order.created"
        )

    def handle(self, event):
        data = event["data"]

        tx_ref = str(uuid.uuid4())

        checkout_url = ChapaService.initialize_payment({
            "amount": data["amount"],
            "currency": data["currency"],
            "email": data["email"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "tx_ref": tx_ref,
            "order_id": data["order_id"]
        })

        Payment.objects.create(
            order_id=data["order_id"],
            amount=data["amount"],
            currency=data["currency"],
            status="pending",
            checkout_url=checkout_url,
            tx_ref=tx_ref
        )


    # def handle(self, event):
    #     event_id = event["event_id"]

    #     # if ProcessedEvent.objects.filter(event_id=event_id).exists():
    #         # print("[Order] Duplicate event ignored")
    #         # return
    #     print("[Payment] Processing order:", event["data"]["order_id"])

    #     # Simulate payment processing
    #     order_id = event["data"]["order_id"]
    #     amount = event["data"]["amount"]

    #     amount = 200
    
    #     # TODO: real payment logic
    #     time.sleep(60)
    #     success = True

    #     if success:
    #         from payments.events import publish_payment_completed
    #         publish_payment_completed(order_id, amount)
    #         ProcessedEvent.objects.create(event_id=event_id)


