#!/bin/bash
# 배포 자동화 스크립트 예시
set -e
cd $(dirname $0)/..
echo "[deploy] git pull"
git pull
echo "[deploy] migrate"
python manage.py migrate
echo "[deploy] collectstatic"
python manage.py collectstatic --noinput
echo "[deploy] reload gunicorn"
systemctl reload gunicorn || true
echo "[deploy] 완료"
