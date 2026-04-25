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

        if event is None:
            print("Received empty event from RabbitMQ. Skipping.")
            return

        # 2. Safety check: Ensure "data" key exists before accessing it
        data = event.get("data")
        if data is None:
            print(f"Event missing 'data' key: {event}")
            return

        required_fields = ["email", "first_name", "last_name"]

        for field in required_fields:
            if not data.get(field):
                print(f"Missing required field: {field}")
                return
        # data = event["data"]

        print("---",data.get("email"),"---")

        tx_ref = str(uuid.uuid4())

        # checkout_url = ChapaService.initialize_payment({
        #     "amount": data["amount"],
        #     "currency": data["currency"],
        #     "email": data["email"],
        #     "first_name": data["first_name"],
        #     "last_name": data["last_name"],
        #     "tx_ref": tx_ref,
        #     "order_id": data["order_id"]
        # })
        
        try:
            checkout_url = ChapaService.initialize_payment({
                "amount": data.get("amount"),
                "currency": data.get("currency"),
                "email": str(data.get("email")).strip(),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "tx_ref": tx_ref,
                "order_id": data.get("order_id")
            })

            if not checkout_url:
                print(f"Chapa initialization failed for Order {data.get('order_id')}")
                return


        # Payment.objects.create(
        #     order_id=data["order_id"],
        #     amount=data["amount"],
        #     currency=data["currency"],
        #     status="pending",
        #     checkout_url=checkout_url,
        #     tx_ref=tx_ref
        # )
            Payment.objects.create(
            order_id=data.get("order_id"),
            amount=data.get("amount"),
            currency=data.get("currency"),
            status="pending",
            checkout_url=checkout_url,
            tx_ref=tx_ref
        )

            print(f"Payment record created for Order {data.get('order_id')}")

        except Exception as e:
            print(f"Error processing order {data.get('order_id')}: {e}")


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


