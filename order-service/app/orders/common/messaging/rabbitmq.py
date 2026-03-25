import os
import pika
import json
import time
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
        self.queue_name = queue_name
        self.routing_key = routing_key

        self.connection = RabbitMQConnection().get_connection()
        self.channel = self.connection.channel()

        # ========================
        # MAIN EXCHANGE
        # ========================
        self.channel.exchange_declare(
            exchange="ecommerce_events",
            exchange_type="topic",
            durable=True
        )

        # ========================
        # DLX (Dead Letter Exchange)
        # ========================
        self.channel.exchange_declare(
            exchange="dlx_exchange",
            exchange_type="topic",
            durable=True
        )

        # ========================
        # DLQ (Dead Letter Queue)
        # ========================
        self.channel.queue_declare(
            queue="dead_letter_queue",
            durable=True
        )

        self.channel.queue_bind(
            exchange="dlx_exchange",
            queue="dead_letter_queue",
            routing_key="#"
        )

        # ========================
        # MAIN QUEUE (with DLQ config)
        # ========================
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "dlx_exchange"
            }
        )

        self.channel.queue_bind(
            exchange="ecommerce_events",
            queue=self.queue_name,
            routing_key=self.routing_key
        )

        # ========================
        # FAIR DISPATCH
        # ========================
        self.channel.basic_qos(prefetch_count=1)

    def start_consuming(self, callback):
        def wrapper(ch, method, properties, body):
            event = json.loads(body)

            retries = 0
            if properties.headers and "x-retry" in properties.headers:
                retries = properties.headers["x-retry"]

            try:
                print(f"[→] {method.routing_key} | Retry: {retries}")

                callback(event)

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                print(f"[ERROR] {e}")

                if retries < 3:
                    print(f"[Retry] Sending back ({retries + 1})")

                    time.sleep(2)

                    ch.basic_publish(
                        exchange="ecommerce_events",
                        routing_key=method.routing_key,
                        body=body,
                        properties=pika.BasicProperties(
                            delivery_mode=2,
                            headers={"x-retry": retries + 1}
                        )
                    )
                else:
                    print("[DLQ] Max retries exceeded → sending to DLQ")

                    ch.basic_publish(
                        exchange="dlx_exchange",
                        routing_key=method.routing_key,
                        body=body,
                        properties=pika.BasicProperties(
                            delivery_mode=2
                        )
                    )

                ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=wrapper
        )

        print(f"[*] Listening on {self.queue_name}...")
        self.channel.start_consuming()