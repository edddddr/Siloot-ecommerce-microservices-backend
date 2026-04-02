#!/bin/sh

echo "Waiting for database..."

while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done

cd /app/app || cd /app

echo "Database started"
python manage.py migrate
exec python manage.py runserver 0.0.0.0:8000