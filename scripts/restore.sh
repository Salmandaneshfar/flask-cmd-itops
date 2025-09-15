#!/bin/bash

# اسکریپت بازیابی دیتابیس
# استفاده: ./restore.sh backup_file.sql.gz

set -e

BACKUP_FILE=$1
DOCKER_COMPOSE_FILE="docker-compose.yml"

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ لطفاً نام فایل بکاپ را مشخص کنید."
    echo "استفاده: ./restore.sh backup_file.sql.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ فایل بکاپ یافت نشد: $BACKUP_FILE"
    exit 1
fi

echo "⚠️ هشدار: این عملیات تمام داده‌های موجود را حذف خواهد کرد!"
read -p "آیا مطمئن هستید؟ (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "❌ عملیات لغو شد."
    exit 1
fi

echo "🔄 شروع بازیابی دیتابیس..."

# متوقف کردن سرویس web
echo "⏹️ متوقف کردن سرویس web..."
docker-compose -f $DOCKER_COMPOSE_FILE stop web

# بازیابی دیتابیس
echo "📊 بازیابی دیتابیس..."
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | docker-compose -f $DOCKER_COMPOSE_FILE exec -T db psql -U cms_user -d cms_db
else
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T db psql -U cms_user -d cms_db < $BACKUP_FILE
fi

# راه‌اندازی مجدد سرویس web
echo "🚀 راه‌اندازی مجدد سرویس web..."
docker-compose -f $DOCKER_COMPOSE_FILE start web

echo "✅ بازیابی با موفقیت تکمیل شد!"







