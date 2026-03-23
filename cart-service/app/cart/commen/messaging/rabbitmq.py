import os
import pika
import json

class RabbitMQConnection:
    def __init__(self):
        self.host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.port = int(os.getenv("RABBITMQ_PORT", 5672))
        self.user = os.getenv("RABBITMQ_USER", "admin")
        self.password = os.getenv("RABBITMQ_PASSWORD", "admin123")

    def get_connection(self):
        credentials = pika.PlainCredentials(self.user, self.password)

        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )

        return pika.BlockingConnection(parameters)


class EventPublisher:
    def __init__(self):
        self.connection = RabbitMQConnection().get_connection()
        self.channel = self.connection.channel()

        # Exchange (important!)
        self.channel.exchange_declare(
            exchange="ecommerce_events",
            exchange_type="topic",
            durable=True
        )

    def publish(self, routing_key, message):
        self.channel.basic_publish(
            exchange="ecommerce_events",
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # persistent
            )
        )

        print(f"[✓] Event published: {routing_key}")


class EventConsumer:
    def __init__(self, queue_name, routing_key):
        self.connection = RabbitMQConnection().get_connection()
        self.channel = self.connection.channel()
        self.queue_name = queue_name
        

        self.channel.exchange_declare(
            exchange="ecommerce_events",
            exchange_type="topic",
            durable=True
        )

        self.channel.queue_declare(queue=self.queue_name, durable=True)

        self.channel.queue_bind(
            exchange="ecommerce_events",
            queue=self.queue_name,
            routing_key=routing_key
        )

    def start_consuming(self, callback):
        def wrapper(ch, method, properties, body):
            print(f"[→] Received: {method.routing_key}")

            callback(json.loads(body))

            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=wrapper
        )

        print("[*] Waiting for messages...")
        self.channel.start_consuming()