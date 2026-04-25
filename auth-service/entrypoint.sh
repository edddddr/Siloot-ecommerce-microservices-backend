#!/bin/sh

echo "Waiting for database..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "Database started"

# Check for RabbitMQ before starting Django/Consumers
echo "Waiting for RabbitMQ..."
while ! nc -z $RABBITMQ_HOST $RABBITMQ_PORT; do
  sleep 1
done
echo "RabbitMQ started"

# Simplified directory change
cd /app

python manage.py migrate   
exec "$@"