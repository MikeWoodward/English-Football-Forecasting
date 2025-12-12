#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate

# Collect static files for production (required for admin panel)
python manage.py collectstatic --noinput

# Only needed the first time a service is brought up
python manage.py createsuperuser --noinput
