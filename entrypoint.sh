#!/bin/sh
set -e

if [ "$DB_HOST" ]; then
    echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
    while ! nc -z "$DB_HOST" "${DB_PORT:-5432}"; do
        sleep 0.5
    done
    echo "PostgreSQL is up and ready!"
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ "$#" -eq 0 ]; then
    exec gunicorn vendorama.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
else
    exec "$@"
fi