#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate

# Only needed the first time a service is brought up
# python manage.py createsuperuser --noinput
