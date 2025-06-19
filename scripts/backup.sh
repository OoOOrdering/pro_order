#!/bin/bash
# DB 백업 자동화 스크립트 예시
set -e
cd $(dirname $0)/..
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=backups
mkdir -p $BACKUP_DIR
echo "[backup] 백업 시작: $DATE"
python manage.py dumpdata --natural-foreign --natural-primary --exclude auth.permission --exclude contenttypes > $BACKUP_DIR/db_backup_$DATE.json
echo "[backup] 완료: $BACKUP_DIR/db_backup_$DATE.json"
