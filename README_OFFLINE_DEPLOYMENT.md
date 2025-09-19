# راهنمای نصب آفلاین Flask CMS روی Red Hat 8.10

## 📋 خلاصه

این راهنما برای نصب Flask CMS روی سرور Red Hat 8.10 **بدون دسترسی اینترنت** طراحی شده است. تمام پکیج‌ها و وابستگی‌ها باید از قبل آماده شوند.

## 🎯 مراحل کلی

### مرحله 1: آماده‌سازی روی سرور با اینترنت

#### 1.1 دانلود پکیج‌های آفلاین
```bash
# روی سروری با دسترسی اینترنت
git clone <repository-url>
cd flask-cms-itop

# اجرای اسکریپت دانلود
chmod +x download-offline-packages.sh
./download-offline-packages.sh
```

#### 1.2 ایجاد آرشیو
```bash
# آرشیو به صورت خودکار ایجاد می‌شود
# نام فایل: flask-cms-offline-packages-YYYYMMDD_HHMMSS.tar.gz
```

### مرحله 2: انتقال به سرور مقصد

#### 2.1 کپی فایل‌ها
```bash
# کپی آرشیو به سرور مقصد
scp flask-cms-offline-packages-*.tar.gz user@target-server:/tmp/

# یا کپی دایرکتوری کامل
scp -r flask-cms-itop/ user@target-server:/tmp/
```

#### 2.2 استخراج آرشیو (در صورت نیاز)
```bash
# روی سرور مقصد
cd /tmp
tar -xzf flask-cms-offline-packages-*.tar.gz
```

### مرحله 3: نصب روی سرور مقصد

#### 3.1 روش خودکار (توصیه شده)
```bash
# روی سرور مقصد
cd /tmp/flask-cms-itop
chmod +x setup-offline.sh
sudo ./setup-offline.sh
```

#### 3.2 روش دستی
```bash
# نصب پکیج‌های RPM
cd /tmp/flask-cms-itop/offline-packages
chmod +x install-rpm-packages.sh
sudo ./install-rpm-packages.sh

# نصب پکیج‌های Python
chmod +x install-python-packages.sh
./install-python-packages.sh

# اجرای اسکریپت نصب اصلی
chmod +x install-redhat.sh
./install-redhat.sh
```

## 📦 فایل‌های مورد نیاز

### فایل‌های اصلی
- `requirements-offline.txt` - لیست وابستگی‌های Python
- `offline-packages-list.txt` - لیست پکیج‌های RPM
- `install-redhat.sh` - اسکریپت نصب اصلی
- `setup-offline.sh` - اسکریپت نصب آفلاین
- `download-offline-packages.sh` - اسکریپت دانلود پکیج‌ها

### فایل‌های پیکربندی
- `config.py` - تنظیمات برنامه
- `production.env` - متغیرهای محیطی
- `nginx/` - تنظیمات Nginx
- `Dockerfile` - (اختیاری) برای Docker

## 🔧 تنظیمات پیش‌نیاز

### مشخصات سرور
- **سیستم عامل:** Red Hat Enterprise Linux 8.10
- **معماری:** x86_64
- **حداقل RAM:** 4GB
- **حداقل فضای دیسک:** 20GB
- **پورت‌های مورد نیاز:** 80, 443, 5000, 5432, 6379

### پکیج‌های سیستم
- Python 3.11
- PostgreSQL 15
- Redis 6
- Nginx
- Development Tools

## 🚀 دستورات سریع

### نصب کامل (یک دستور)
```bash
# روی سرور با اینترنت
./download-offline-packages.sh

# انتقال به سرور مقصد
scp flask-cms-offline-packages-*.tar.gz user@target-server:/tmp/

# روی سرور مقصد
cd /tmp && tar -xzf flask-cms-offline-packages-*.tar.gz
cd offline-packages && sudo ./setup-offline.sh
```

### بررسی وضعیت
```bash
# وضعیت سرویس‌ها
systemctl status flask-cms postgresql-15 redis6 nginx

# تست برنامه
curl http://localhost/health

# مشاهده لاگ‌ها
journalctl -u flask-cms -f
```

## 🛠️ عیب‌یابی

### مشکلات رایج

#### 1. خطای نصب پکیج‌های RPM
```bash
# بررسی وابستگی‌ها
rpm -qpR package-name.rpm

# نصب با نادیده گرفتن وابستگی‌ها (خطرناک)
rpm -Uvh --nodeps package-name.rpm
```

#### 2. خطای نصب پکیج‌های Python
```bash
# بررسی فایل‌های موجود
ls -la offline-packages/python-packages/

# نصب دستی
pip install --no-index --find-links . package-name
```

#### 3. خطای اتصال به دیتابیس
```bash
# بررسی وضعیت PostgreSQL
systemctl status postgresql-15

# بررسی لاگ‌ها
tail -f /var/lib/pgsql/15/data/log/postgresql-*.log
```

#### 4. خطای اتصال به Redis
```bash
# بررسی وضعیت Redis
systemctl status redis6

# تست اتصال
redis-cli ping
```

## 📊 مانیتورینگ

### اسکریپت مانیتورینگ
```bash
#!/bin/bash
# /opt/flask-cms/scripts/monitor.sh

echo "=== Flask CMS System Status ==="
echo "Date: $(date)"
echo ""

echo "=== Services Status ==="
systemctl is-active flask-cms postgresql-15 redis6 nginx

echo ""
echo "=== Disk Usage ==="
df -h /opt/flask-cms /var/lib/pgsql /var/lib/redis

echo ""
echo "=== Memory Usage ==="
free -h

echo ""
echo "=== Application Health ==="
curl -s http://localhost/health | python3 -m json.tool
```

## 🔒 امنیت

### تنظیمات امنیتی
1. **تغییر رمزهای پیش‌فرض**
2. **فعال‌سازی فایروال**
3. **تنظیم SSL**
4. **محدود کردن دسترسی SSH**

### دستورات امنیتی
```bash
# تغییر رمز admin
sudo -u cms /home/cms/venv/bin/python -c "
from /opt/flask-cms.app import create_app, db, User
app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.set_password('new-password')
    db.session.commit()
"

# تنظیم فایروال
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload
```

## 📞 پشتیبانی

### لاگ‌های مهم
- **برنامه:** `journalctl -u flask-cms`
- **PostgreSQL:** `/var/lib/pgsql/15/data/log/`
- **Redis:** `journalctl -u redis6`
- **Nginx:** `/var/log/nginx/`

### دستورات مفید
```bash
# بکاپ دیتابیس
sudo -u postgres pg_dump cms_db > backup_$(date +%Y%m%d_%H%M%S).sql

# بازیابی دیتابیس
sudo -u postgres psql cms_db < backup_file.sql

# به‌روزرسانی برنامه
systemctl stop flask-cms
# کپی فایل‌های جدید
systemctl start flask-cms
```

## 📋 چک‌لیست نصب

- [ ] سرور Red Hat 8.10 آماده است
- [ ] پکیج‌های آفلاین دانلود شده‌اند
- [ ] فایل‌ها به سرور مقصد منتقل شده‌اند
- [ ] اسکریپت نصب اجرا شده است
- [ ] سرویس‌ها راه‌اندازی شده‌اند
- [ ] برنامه تست شده است
- [ ] تنظیمات امنیتی اعمال شده‌اند
- [ ] بکاپ اولیه ایجاد شده است

---

**توسعه داده شده با ❤️ برای محیط‌های آفلاین**



