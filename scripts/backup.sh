#!/bin/bash

# اسکریپت بکاپ از دیتابیس
# استفاده: ./backup.sh [backup_name]

set -e

BACKUP_NAME=${1:-backup_$(date +%Y%m%d_%H%M%S)}
BACKUP_DIR="backups"
DOCKER_COMPOSE_FILE="docker-compose.yml"

echo "💾 شروع بکاپ از دیتابیس..."

# بررسی وجود دایرکتوری بکاپ
mkdir -p $BACKUP_DIR

# ایجاد بکاپ از دیتابیس
echo "📊 ایجاد بکاپ از PostgreSQL..."
docker-compose -f $DOCKER_COMPOSE_FILE exec -T db pg_dump -U cms_user cms_db > $BACKUP_DIR/${BACKUP_NAME}.sql

# فشرده‌سازی بکاپ
echo "🗜️ فشرده‌سازی بکاپ..."
gzip $BACKUP_DIR/${BACKUP_NAME}.sql

# حذف بکاپ‌های قدیمی (بیش از 7 روز)
echo "🧹 حذف بکاپ‌های قدیمی..."
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "✅ بکاپ با موفقیت ایجاد شد: $BACKUP_DIR/${BACKUP_NAME}.sql.gz"

# نمایش حجم بکاپ
ls -lh $BACKUP_DIR/${BACKUP_NAME}.sql.gz











