import os
import pika
import json
import logging
from pika.exceptions import AMQPConnectionError, AMQPChannelError

logger = logging.getLogger(__name__)

class RabbitMQConnection:
    """Singleton-style connection management to prevent socket exhaustion."""
    _connection = None

    @classmethod
    def get_connection(cls):
        if cls._connection is None or cls._connection.is_closed:
            host = os.getenv("RABBITMQ_HOST", "rabbitmq")
            port = int(os.getenv("RABBITMQ_PORT", 5672))
            user = os.getenv("RABBITMQ_USER", "admin")
            password = os.getenv("RABBITMQ_PASSWORD", "admin123")

            credentials = pika.PlainCredentials(user, password)
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            try:
                cls._connection = pika.BlockingConnection(parameters)
                logger.info("Connected to RabbitMQ")
            except AMQPConnectionError as e:
                logger.error(f"Could not connect to RabbitMQ: {e}")
                raise
        return cls._connection


class EventPublisher:
    def __init__(self):
        self.exchange = "ecommerce_events"
        self._setup_exchange()

    def _setup_exchange(self):
        try:
            connection = RabbitMQConnection.get_connection()
            self.channel = connection.channel()
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type="topic",
                durable=True
            )
        except (AMQPConnectionError, AMQPChannelError) as e:
            logger.critical(f"RabbitMQ Publisher setup failed: {e}")

    def publish(self, routing_key, message):
        """Publishes a persistent message to the exchange."""
        try:
            # Ensure channel is open
            if not self.channel or self.channel.is_closed:
                self._setup_exchange()

            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Event published: {routing_key}", extra={"routing_key": routing_key})
        except Exception as e:
            logger.error(f"Failed to publish event {routing_key}: {e}")
            # In EKS, you might want to raise this so the Order transaction rolls back
            raise 

class EventConsumer:
    """
    Consumer with built-in Retry logic and Dead Letter Queue (DLQ).
    """
    def __init__(self, queue_name, routing_key):
        self.queue_name = queue_name
        self.routing_key = routing_key
        self._setup_infrastructure()

    def _setup_infrastructure(self):
        connection = RabbitMQConnection.get_connection()
        self.channel = connection.channel()

        # 1. Main Exchange
        self.channel.exchange_declare(exchange="ecommerce_events", exchange_type="topic", durable=True)

        # 2. DLX (Dead Letter Exchange)
        self.channel.exchange_declare(exchange="dlx_exchange", exchange_type="topic", durable=True)

        # 3. DLQ (Dead Letter Queue) - where messages go after 3 failures
        self.channel.queue_declare(queue="dead_letter_queue", durable=True)
        self.channel.queue_bind(exchange="dlx_exchange", queue="dead_letter_queue", routing_key="#")

        # 4. Main Queue with DLX configuration
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            arguments={"x-dead-letter-exchange": "dlx_exchange"}
        )
        self.channel.queue_bind(exchange="ecommerce_events", queue=self.queue_name, routing_key=self.routing_key)
        
        # Fair dispatch: don't give more than 1 message to a worker at a time
        self.channel.basic_qos(prefetch_count=1)

    def start_consuming(self, callback):
        def wrapper(ch, method, properties, body):
            event = json.loads(body)
            # Safe header extraction
            headers = properties.headers or {}
            retries = headers.get("x-retry", 0)

            try:
                logger.info(f"Processing {method.routing_key} (Retry: {retries})")
                callback(event)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                if retries < 3:
                    # Exponential backoff would be better, but simple retry for now
                    ch.basic_publish(
                        exchange="ecommerce_events",
                        routing_key=method.routing_key,
                        body=body,
                        properties=pika.BasicProperties(
                            delivery_mode=2,
                            headers={"x-retry": retries + 1}
                        )
                    )
                    logger.info(f"Re-queued for retry {retries + 1}")
                else:
                    # Manual move to DLQ
                    logger.critical("Max retries reached. Moving to DLQ.")
                    ch.basic_publish(
                        exchange="dlx_exchange",
                        routing_key=method.routing_key,
                        body=body,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                
                # Acknowledge the old message so it doesn't stay in the main queue
                ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(queue=self.queue_name, on_message_callback=wrapper)
        logger.info(f"Listening on {self.queue_name}...")
        self.channel.start_consuming()