#!/bin/bash

# اسکریپت deployment برای سرورهای Linux
# استفاده: ./deploy.sh [environment]

set -e

# تنظیمات
ENVIRONMENT=${1:-production}
PROJECT_NAME="flask-cms"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="backups"
LOG_DIR="logs"

echo "🚀 شروع deployment برای محیط $ENVIRONMENT"

# بررسی وجود Docker و Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker نصب نیست. لطفاً ابتدا Docker را نصب کنید."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose نصب نیست. لطفاً ابتدا Docker Compose را نصب کنید."
    exit 1
fi

# ایجاد دایرکتوری‌های مورد نیاز
echo "📁 ایجاد دایرکتوری‌های مورد نیاز..."
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR
mkdir -p static/uploads
mkdir -p ssl

# کپی فایل .env اگر وجود ندارد
if [ ! -f .env ]; then
    echo "📋 کپی فایل env.example به .env..."
    cp env.example .env
    echo "⚠️ لطفاً فایل .env را ویرایش کنید و تنظیمات مناسب را وارد کنید."
    echo "🔑 خصوصاً SECRET_KEY را تغییر دهید!"
    read -p "آیا فایل .env را ویرایش کرده‌اید؟ (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ لطفاً ابتدا فایل .env را ویرایش کنید."
        exit 1
    fi
fi

# ایجاد SSL certificate خودامضا (برای تست)
if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
    echo "🔐 ایجاد SSL certificate خودامضا..."
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=IR/ST=Tehran/L=Tehran/O=CMS/OU=IT/CN=localhost"
fi

# بکاپ از دیتابیس موجود (اگر وجود دارد)
if [ -f instance/cms.db ]; then
    echo "💾 ایجاد بکاپ از دیتابیس موجود..."
    cp instance/cms.db backups/cms_backup_$(date +%Y%m%d_%H%M%S).db
fi

# متوقف کردن containerهای موجود
echo "⏹️ متوقف کردن containerهای موجود..."
docker-compose -f $DOCKER_COMPOSE_FILE down || true

# حذف imageهای قدیمی (اختیاری)
echo "🧹 پاکسازی imageهای قدیمی..."
docker image prune -f || true

# ساخت و اجرای containerها
echo "🔨 ساخت و اجرای containerها..."
docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache
docker-compose -f $DOCKER_COMPOSE_FILE up -d

# انتظار برای آماده شدن سرویس‌ها
echo "⏳ انتظار برای آماده شدن سرویس‌ها..."
sleep 30

# بررسی وضعیت سرویس‌ها
echo "🔍 بررسی وضعیت سرویس‌ها..."
docker-compose -f $DOCKER_COMPOSE_FILE ps

# بررسی health check
echo "🏥 بررسی health check..."
for i in {1..10}; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ سرویس‌ها با موفقیت راه‌اندازی شدند!"
        break
    else
        echo "⏳ انتظار... ($i/10)"
        sleep 10
    fi
done

# نمایش اطلاعات دسترسی
echo ""
echo "🎉 Deployment با موفقیت تکمیل شد!"
echo ""
echo "📊 اطلاعات دسترسی:"
echo "   🌐 وب سایت: http://localhost"
echo "   🔧 pgAdmin: http://localhost:8080"
echo "   📊 Health Check: http://localhost/health"
echo ""
echo "👤 اطلاعات ورود پیش‌فرض:"
echo "   نام کاربری: admin"
echo "   رمز عبور: admin123"
echo ""
echo "📋 دستورات مفید:"
echo "   مشاهده لاگ‌ها: docker-compose logs -f"
echo "   متوقف کردن: docker-compose down"
echo "   راه‌اندازی مجدد: docker-compose up -d"
echo "   بکاپ دیتابیس: docker-compose exec db pg_dump -U cms_user cms_db > backup.sql"
echo ""

