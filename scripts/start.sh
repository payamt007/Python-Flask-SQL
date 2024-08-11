#!/bin/bash

/bin/sh -c "until nc -z db 5432; do sleep 1; done"
python /files/scripts/insert_admin_user.py
/bin/sh -c "gunicorn wsgi:application --bind 0.0.0.0:8000"