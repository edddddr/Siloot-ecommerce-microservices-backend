import uuid
from datetime import datetime
from payments.common.messaging.rabbitmq import EventPublisher


def publish_payment_completed(event_type, order_id): #,amount
    publisher = EventPublisher()

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "order_id": order_id,
            # "amount": amount
        }
    }

    publisher.publish("payment.completed", event)