# راهنمای Deployment - Flask CMS

## 🚀 راه‌اندازی سریع

### روش 1: Docker (توصیه شده)

```bash
# 1. کلون کردن پروژه
git clone <repository-url>
cd flask-cms-itop

# 2. تنظیم متغیرهای محیطی
cp env.example .env
# ویرایش فایل .env

# 3. راه‌اندازی
make setup
make dev
```

### روش 2: نصب دستی

```bash
# 1. ایجاد محیط مجازی
python -m venv venv
source venv/bin/activate  # Linux/Mac
# یا
venv\Scripts\activate     # Windows

# 2. نصب وابستگی‌ها
pip install -r requirements.txt

# 3. راه‌اندازی دیتابیس
python run.py init

# 4. اجرای سرور
python run.py
```

## 🔧 تنظیمات Production

### 1. متغیرهای محیطی

فایل `.env` را ویرایش کنید:

```bash
# امنیت
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production

# دیتابیس
DB_PASSWORD=your-secure-password
DATABASE_URL=postgresql://cms_user:${DB_PASSWORD}@localhost:5432/cms_db

# Redis
REDIS_URL=redis://localhost:6379/0

# ایمیل
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourdomain.com
```

### 2. SSL Certificate

```bash
# ایجاد دایرکتوری SSL
mkdir ssl

# ایجاد certificate خودامضا (برای تست)
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=IR/ST=Tehran/L=Tehran/O=CMS/OU=IT/CN=yourdomain.com"

# یا استفاده از Let's Encrypt
certbot certonly --standalone -d yourdomain.com
```

### 3. اجرای Production

```bash
# با Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# یا با Makefile
make prod
```

## 📊 مانیتورینگ

### دستورات مفید

```bash
# مشاهده وضعیت
make status

# مشاهده لاگ‌ها
make logs

# مانیتورینگ سیستم
make monitor

# بکاپ دیتابیس
make backup

# بازیابی دیتابیس
make restore FILE=backup_file.sql.gz
```

### Health Check

```bash
# بررسی سلامت سیستم
curl http://localhost/health

# پاسخ نمونه:
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy",
  "timestamp": "2025-09-14T14:42:39.199672"
}
```

## 🔒 امنیت

### تنظیمات امنیتی

1. **تغییر رمزهای پیش‌فرض:**
   ```bash
   # تغییر رمز admin
   python -c "from app import create_app, db, User; app = create_app(); app.app_context().push(); admin = User.query.filter_by(username='admin').first(); admin.set_password('new-password'); db.session.commit()"
   ```

2. **فعال‌سازی Firewall:**
   ```bash
   # Ubuntu/Debian
   ufw allow 22
   ufw allow 80
   ufw allow 443
   ufw enable
   ```

3. **تنظیم Nginx:**
   - Rate limiting فعال است
   - Security headers اضافه شده
   - SSL termination

## 🐳 Docker Commands

```bash
# ساخت image
docker-compose build

# اجرای سرویس‌ها
docker-compose up -d

# متوقف کردن
docker-compose down

# مشاهده لاگ‌ها
docker-compose logs -f

# دسترسی به container
docker-compose exec web bash

# بکاپ دیتابیس
docker-compose exec db pg_dump -U cms_user cms_db > backup.sql
```

## 📁 ساختار فایل‌ها

```
flask-cms-itop/
├── app.py                 # فایل اصلی Flask
├── config.py              # تنظیمات
├── models.py              # مدل‌های دیتابیس
├── forms.py               # فرم‌های WTForms
├── logging_config.py      # تنظیمات logging
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose (development)
├── docker-compose.prod.yml # Docker Compose (production)
├── Makefile               # دستورات مدیریت
├── deploy.sh              # اسکریپت deployment (Linux/Mac)
├── deploy.bat             # اسکریپت deployment (Windows)
├── nginx/                 # تنظیمات Nginx
├── scripts/               # اسکریپت‌های مدیریت
├── logs/                  # فایل‌های لاگ
├── backups/               # بکاپ‌های دیتابیس
└── static/                # فایل‌های استاتیک
```

## 🆘 عیب‌یابی

### مشکلات رایج

1. **خطای Import:**
   ```bash
   pip install -r requirements.txt
   ```

2. **خطای دیتابیس:**
   ```bash
   python run.py init
   ```

3. **خطای Redis:**
   ```bash
   # Redis اختیاری است، می‌توانید حذف کنید
   ```

4. **خطای SSL:**
   ```bash
   # برای development از HTTP استفاده کنید
   ```

### لاگ‌ها

```bash
# لاگ‌های برنامه
tail -f logs/app.log

# لاگ‌های امنیت
tail -f logs/security.log

# لاگ‌های Docker
docker-compose logs -f
```

## 📞 پشتیبانی

برای گزارش مشکل یا درخواست کمک:
- GitHub Issues
- Email: admin@yourdomain.com

---

**توسعه داده شده با ❤️ توسط تیم Flask CMS**







