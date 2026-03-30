#!/bin/sh

echo "Waiting for database..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done

echo "Waiting for RabbitMQ..."
# Using the vars from your RabbitMQConnection class
while ! nc -z $RABBITMQ_HOST 5672; do
  sleep 0.1
done


cd /app || cd /app/app  

echo "Services started"
python manage.py migrate
exec python manage.py runserver 0.0.0.0:8000