from django.core.management.base import BaseCommand
from orders.consumers.payment_consumer import PaymentCompletedConsumer

class Command(BaseCommand):
    help = "Run RabbitMQ consumers"
    print("wainting to ")

    def handle(self, *args, **kwargs):
        consumer = PaymentCompletedConsumer()
        consumer.start_consuming(consumer.handle)