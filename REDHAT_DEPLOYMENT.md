# راهنمای Deployment روی سرور Red Hat 8.10 (بدون دسترسی اینترنت)

## 📋 پیش‌نیازهای سیستم

### 1. مشخصات سرور
- **سیستم عامل:** Red Hat Enterprise Linux 8.10
- **معماری:** x86_64
- **حداقل RAM:** 4GB (توصیه: 8GB)
- **حداقل فضای دیسک:** 20GB (توصیه: 50GB)
- **پورت‌های مورد نیاز:** 80, 443, 5000, 5432, 6379

### 2. پکیج‌های سیستم مورد نیاز

#### پکیج‌های پایه RHEL:
```bash
# Python و ابزارهای توسعه
python3.11
python3.11-pip
python3.11-devel
python3.11-setuptools
python3.11-wheel

# ابزارهای build
gcc
gcc-c++
make
cmake
pkg-config

# کتابخانه‌های سیستم
openssl-devel
libffi-devel
zlib-devel
bzip2-devel
readline-devel
sqlite-devel
tk-devel
gdbm-devel
db4-devel
libpcap-devel
xz-devel
expat-devel
libuuid-devel
libxml2-devel
libxslt-devel

# PostgreSQL
postgresql15-server
postgresql15-devel
postgresql15-contrib

# Redis
redis6
redis6-devel

# Nginx
nginx

# ابزارهای امنیت
openssl
certbot
```

## 🚀 مراحل نصب

### مرحله 1: آماده‌سازی سرور

#### 1.1 نصب پکیج‌های پایه
```bash
# فعال‌سازی EPEL repository
sudo subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
sudo subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
sudo dnf install -y epel-release

# نصب پکیج‌های مورد نیاز
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y python3.11 python3.11-pip python3.11-devel
sudo dnf install -y gcc gcc-c++ make cmake pkg-config
sudo dnf install -y openssl-devel libffi-devel zlib-devel
sudo dnf install -y postgresql15-server postgresql15-devel
sudo dnf install -y redis6 redis6-devel
sudo dnf install -y nginx openssl
```

#### 1.2 تنظیم فایروال
```bash
# فعال‌سازی فایروال
sudo systemctl enable firewalld
sudo systemctl start firewalld

# باز کردن پورت‌های مورد نیاز
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --permanent --add-port=6379/tcp
sudo firewall-cmd --reload
```

### مرحله 2: نصب و تنظیم PostgreSQL

```bash
# راه‌اندازی اولیه PostgreSQL
sudo postgresql-15-setup initdb
sudo systemctl enable postgresql-15
sudo systemctl start postgresql-15

# ایجاد کاربر و دیتابیس
sudo -u postgres psql << EOF
CREATE USER cms_user WITH PASSWORD 'cms_password';
CREATE DATABASE cms_db OWNER cms_user;
GRANT ALL PRIVILEGES ON DATABASE cms_db TO cms_user;
\q
EOF

# تنظیم pg_hba.conf برای دسترسی محلی
sudo sed -i "s/#local   all             all                                     peer/local   all             all                                     md5/" /var/lib/pgsql/15/data/pg_hba.conf
sudo systemctl restart postgresql-15
```

### مرحله 3: نصب و تنظیم Redis

```bash
# راه‌اندازی Redis
sudo systemctl enable redis6
sudo systemctl start redis6

# تنظیم Redis برای persistence
sudo sed -i 's/^# save 900 1/save 900 1/' /etc/redis6.conf
sudo sed -i 's/^# save 300 10/save 300 10/' /etc/redis6.conf
sudo sed -i 's/^# save 60 10000/save 60 10000/' /etc/redis6.conf
sudo systemctl restart redis6
```

### مرحله 4: نصب Python و وابستگی‌ها

#### 4.1 ایجاد محیط مجازی
```bash
# ایجاد کاربر مخصوص برنامه
sudo useradd -m -s /bin/bash cms
sudo usermod -aG wheel cms

# تغییر به کاربر cms
sudo su - cms

# ایجاد محیط مجازی
python3.11 -m venv /home/cms/venv
source /home/cms/venv/bin/activate

# ارتقای pip
pip install --upgrade pip setuptools wheel
```

#### 4.2 نصب وابستگی‌های Python (آفلاین)
```bash
# استفاده از فایل requirements-offline.txt
pip install --no-index --find-links ./offline-packages -r requirements-offline.txt
```

### مرحله 5: تنظیم Nginx

```bash
# کپی فایل‌های تنظیمات Nginx
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo cp nginx/conf.d/flask-cms.conf /etc/nginx/conf.d/

# ایجاد دایرکتوری‌های مورد نیاز
sudo mkdir -p /var/www/static
sudo mkdir -p /var/log/nginx
sudo mkdir -p /etc/nginx/ssl

# تنظیم مجوزها
sudo chown -R nginx:nginx /var/www/static
sudo chown -R nginx:nginx /var/log/nginx

# تست تنظیمات
sudo nginx -t

# راه‌اندازی Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### مرحله 6: راه‌اندازی برنامه

#### 6.1 کپی فایل‌های برنامه
```bash
# کپی فایل‌های برنامه به سرور
sudo mkdir -p /opt/flask-cms
sudo cp -r * /opt/flask-cms/
sudo chown -R cms:cms /opt/flask-cms
```

#### 6.2 تنظیم متغیرهای محیطی
```bash
# کپی فایل تنظیمات
sudo cp /opt/flask-cms/production.env /opt/flask-cms/.env

# ویرایش تنظیمات
sudo nano /opt/flask-cms/.env
```

#### 6.3 ایجاد systemd service
```bash
# ایجاد فایل سرویس
sudo tee /etc/systemd/system/flask-cms.service > /dev/null << EOF
[Unit]
Description=Flask CMS Application
After=network.target postgresql-15.service redis6.service

[Service]
Type=exec
User=cms
Group=cms
WorkingDirectory=/opt/flask-cms
Environment=PATH=/home/cms/venv/bin
ExecStart=/home/cms/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 120 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# فعال‌سازی و راه‌اندازی سرویس
sudo systemctl daemon-reload
sudo systemctl enable flask-cms
sudo systemctl start flask-cms
```

### مرحله 7: تنظیم SSL (اختیاری)

```bash
# ایجاد certificate خودامضا
sudo openssl req -x509 -newkey rsa:4096 -keyout /etc/nginx/ssl/key.pem -out /etc/nginx/ssl/cert.pem -days 365 -nodes -subj "/C=IR/ST=Tehran/L=Tehran/O=CMS/OU=IT/CN=yourdomain.com"

# تنظیم مجوزها
sudo chmod 600 /etc/nginx/ssl/key.pem
sudo chmod 644 /etc/nginx/ssl/cert.pem
sudo chown root:root /etc/nginx/ssl/*
```

## 🔧 دستورات مدیریت

### بررسی وضعیت سرویس‌ها
```bash
# وضعیت کلی
sudo systemctl status flask-cms postgresql-15 redis6 nginx

# لاگ‌های برنامه
sudo journalctl -u flask-cms -f

# لاگ‌های Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### مدیریت دیتابیس
```bash
# بکاپ دیتابیس
sudo -u postgres pg_dump cms_db > backup_$(date +%Y%m%d_%H%M%S).sql

# بازیابی دیتابیس
sudo -u postgres psql cms_db < backup_file.sql

# دسترسی به دیتابیس
sudo -u postgres psql -d cms_db
```

### به‌روزرسانی برنامه
```bash
# متوقف کردن سرویس
sudo systemctl stop flask-cms

# بکاپ از فایل‌های فعلی
sudo cp -r /opt/flask-cms /opt/flask-cms.backup.$(date +%Y%m%d_%H%M%S)

# کپی فایل‌های جدید
sudo cp -r new-version/* /opt/flask-cms/
sudo chown -R cms:cms /opt/flask-cms

# راه‌اندازی مجدد
sudo systemctl start flask-cms
```

## 🛠️ عیب‌یابی

### مشکلات رایج

#### 1. خطای اتصال به دیتابیس
```bash
# بررسی وضعیت PostgreSQL
sudo systemctl status postgresql-15

# بررسی لاگ‌های PostgreSQL
sudo tail -f /var/lib/pgsql/15/data/log/postgresql-*.log

# تست اتصال
sudo -u postgres psql -d cms_db -c "SELECT 1;"
```

#### 2. خطای اتصال به Redis
```bash
# بررسی وضعیت Redis
sudo systemctl status redis6

# تست اتصال
redis-cli ping
```

#### 3. خطای Nginx
```bash
# تست تنظیمات
sudo nginx -t

# بررسی لاگ‌ها
sudo tail -f /var/log/nginx/error.log
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

### تنظیمات امنیتی اضافی

#### 1. محدود کردن دسترسی SSH
```bash
# ویرایش /etc/ssh/sshd_config
sudo nano /etc/ssh/sshd_config

# اضافه کردن:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes

# راه‌اندازی مجدد SSH
sudo systemctl restart sshd
```

#### 2. تنظیم SELinux
```bash
# بررسی وضعیت SELinux
sestatus

# تنظیم context برای فایل‌های برنامه
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_connect_db 1
```

#### 3. تنظیم fail2ban
```bash
# نصب fail2ban
sudo dnf install -y fail2ban

# تنظیم fail2ban برای Nginx
sudo tee /etc/fail2ban/jail.d/nginx.conf > /dev/null << EOF
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 📞 پشتیبانی

برای گزارش مشکل یا درخواست کمک:
- بررسی لاگ‌های سیستم
- اجرای اسکریپت مانیتورینگ
- بررسی وضعیت سرویس‌ها

---

**توسعه داده شده با ❤️ برای سرورهای Red Hat Enterprise Linux**

