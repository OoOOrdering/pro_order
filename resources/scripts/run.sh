#!/bin/sh
set -e
# 실행 전에 migrate 자동실행
python3 manage.py migrate
gunicorn --bind 0.0.0.0:8000 config.wsgi:application --workers 2
#gunicorn config.wsgi:application \
#    --bind 0.0.0.0:8000 \
#    --workers 3 \
#    --timeout 120