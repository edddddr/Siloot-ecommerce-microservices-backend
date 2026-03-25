import json
from payments.common.messaging.rabbitmq import EventConsumer
from payments.models import ProcessedEvent
import time

class OrderCreatedConsumer(EventConsumer):
    def __init__(self):
        super().__init__(
            queue_name="payment_order_created",
            routing_key="order.created"
        )

    def handle(self, event):
        event_id = event["event_id"]

        # if ProcessedEvent.objects.filter(event_id=event_id).exists():
            # print("[Order] Duplicate event ignored")
            # return
        print("[Payment] Processing order:", event["data"]["order_id"])

        # Simulate payment processing
        order_id = event["data"]["order_id"]
        amount = event["data"]["amount"]

        amount = 200
    
        # TODO: real payment logic
        time.sleep(60)
        success = True

        if success:
            from payments.events import publish_payment_completed
            publish_payment_completed(order_id, amount)
            ProcessedEvent.objects.create(event_id=event_id)

