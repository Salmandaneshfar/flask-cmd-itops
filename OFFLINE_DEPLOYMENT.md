# راهنمای نصب آفلاین - Flask CMS iTop

این راهنمای نصب برای محیط‌های عملیاتی بدون دسترسی به اینترنت طراحی شده است.

## پیش‌نیازها

### 1. سیستم عامل
- Rocky Linux 8.5 یا بالاتر
- Python 3.11 یا بالاتر
- Docker و Docker Compose (برای نصب Docker-based)

### 2. پکیج‌های مورد نیاز

#### برای نصب با Python venv:
```bash
# Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

#### برای نصب با Docker:
```bash
# Docker و Docker Compose باید از قبل نصب باشند
docker --version
docker compose version
```

## روش‌های نصب آفلاین

### روش 1: نصب با Docker (توصیه می‌شود)

#### مرحله 1: آماده‌سازی فایل‌ها
```bash
# کپی تمام فایل‌های پروژه به سرور
cd /opt/flask-cms-itop

# اطمینان از وجود فایل‌های Docker
ls -la Dockerfile docker-compose.yml docker/entrypoint.sh
```

#### مرحله 2: ساخت فایل .env.docker
```bash
# کپی فایل نمونه
cp docker/env.docker.sample .env.docker

# تولید SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32 | tr -d '\n')
sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env.docker

# تولید CREDENTIALS_KEY
# اگر Python و cryptography در دسترس است:
CREDENTIALS_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null)
# یا با استفاده از Docker:
CREDENTIALS_KEY=$(docker run --rm python:3.11-slim python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
sed -i "s|CREDENTIALS_KEY=.*|CREDENTIALS_KEY=$CREDENTIALS_KEY|g" .env.docker
```

#### مرحله 3: ساخت و اجرای کانتینرها
```bash
# ساخت image (نیاز به اینترنت برای اولین بار - یا استفاده از image از پیش دانلود شده)
docker compose build

# یا اگر image از قبل ساخته شده:
docker load < flask-cms-itop-image.tar  # اگر image را export کرده‌اید

# اجرای کانتینرها
docker compose up -d

# بررسی وضعیت
docker compose ps
docker compose logs -f flask
```

#### مرحله 4: آماده‌سازی برای آفلاین (Export Docker Images)
```bash
# در محیط با اینترنت:
docker compose build
docker save $(docker compose config | grep image: | awk '{print $2}') -o flask-cms-itop-images.tar

# انتقال به سرور آفلاین و لود:
docker load < flask-cms-itop-images.tar
```

### روش 2: نصب با Python venv (بدون Docker)

#### مرحله 1: آماده‌سازی محیط Python
```bash
cd /opt/flask-cms-itop

# ساخت virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# نصب pip wheel
pip install --upgrade pip wheel setuptools
```

#### مرحله 2: نصب پکیج‌ها (آفلاین)
```bash
# اگر wheel files از قبل آماده شده‌اند:
pip install --no-index --find-links ./wheels -r requirements.txt

# یا اگر tar.gz files دارید:
pip install --no-index --find-links ./packages -r requirements.txt
```

#### مرحله 3: آماده‌سازی پکیج‌ها برای آفلاین
```bash
# در محیط با اینترنت:
mkdir -p wheels packages
pip download -r requirements.txt -d wheels
pip wheel -r requirements.txt -w wheels

# یا دانلود tar.gz:
pip download -r requirements.txt -d packages

# انتقال wheels/packages به سرور آفلاین
```

#### مرحله 4: ساخت فایل .env
```bash
# کپی فایل نمونه
cp .env.sample .env  # اگر وجود دارد

# یا ساخت دستی:
cat > .env <<EOF
FLASK_ENV=production
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
CREDENTIALS_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
UPLOAD_FOLDER=static/uploads
DATABASE_URL=sqlite:///instance/cms.db
EOF
```

#### مرحله 5: راه‌اندازی دیتابیس
```bash
# فعال‌سازی venv
source .venv/bin/activate

# ساخت دیتابیس
flask db upgrade

# یا اگر Flask-Migrate نصب نیست:
python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"
```

#### مرحله 6: ساخت دایرکتوری‌های لازم
```bash
mkdir -p instance static/uploads logs
chmod 755 instance static/uploads logs
```

#### مرحله 7: اجرا با Gunicorn
```bash
# نصب Gunicorn (اگر نصب نشده)
pip install --no-index --find-links ./wheels gunicorn

# اجرا
gunicorn -c gunicorn.conf.py wsgi:application

# یا با systemd (فایل deploy/systemd-flask-cms-itop.service)
sudo cp deploy/systemd-flask-cms-itop.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now flask-cms-itop
```

## ساخت User اولیه (Admin)

```bash
# فعال‌سازی venv
source .venv/bin/activate

# ساخت admin user
python <<EOF
from app import create_app, db
from models import User
app = create_app('production')
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin', is_active=True)
        admin.set_password('admin123')  # تغییر دهید!
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin / admin123")
    else:
        print("Admin user already exists")
EOF
```

## پیکربندی Nginx

```bash
# کپی فایل تنظیمات
sudo cp deploy/nginx-flask-cms-itop.conf /etc/nginx/conf.d/

# تست تنظیمات
sudo nginx -t

# راه‌اندازی
sudo systemctl reload nginx
```

## بررسی سلامت سیستم

```bash
# بررسی سرویس‌ها
sudo systemctl status flask-cms-itop
sudo systemctl status nginx

# بررسی لاگ‌ها
sudo journalctl -u flask-cms-itop -f
tail -f logs/app.log

# تست دسترسی
curl http://localhost:8000
curl http://localhost
```

## نکات مهم برای محیط آفلاین

1. **Docker Images**: اگر از Docker استفاده می‌کنید، باید images را از قبل export کرده و به سرور آفلاین منتقل کنید.

2. **Python Wheels**: برای نصب آفلاین Python packages، باید wheel files را از قبل آماده کنید.

3. **Static Files**: مطمئن شوید که تمام فایل‌های static در `static/` موجود هستند.

4. **Database**: دیتابیس SQLite در `instance/cms.db` ذخیره می‌شود. برای backup:
   ```bash
   cp instance/cms.db instance/cms.db.backup.$(date +%Y%m%d_%H%M%S)
   ```

5. **Logs**: لاگ‌ها در `logs/` ذخیره می‌شوند. مطمئن شوید که دسترسی نوشتن وجود دارد.

6. **Permissions**: 
   ```bash
   chown -R rocky:rocky /opt/flask-cms-itop/instance
   chown -R rocky:rocky /opt/flask-cms-itop/logs
   chown -R rocky:rocky /opt/flask-cms-itop/static/uploads
   ```

## Troubleshooting

### مشکل: ModuleNotFoundError
```bash
# بررسی نصب پکیج‌ها
pip list
pip install --no-index --find-links ./wheels <package_name>
```

### مشکل: Database locked
```bash
# بررسی process های در حال استفاده
lsof instance/cms.db
# یا restart سرویس
sudo systemctl restart flask-cms-itop
```

### مشکل: Permission denied
```bash
# تنظیم مجدد دسترسی‌ها
sudo chown -R rocky:rocky /opt/flask-cms-itop
sudo chmod -R 755 /opt/flask-cms-itop
```

## Export برای محیط آفلاین

### ساخت Archive کامل
```bash
# در محیط با اینترنت یا توسعه:
tar -czf flask-cms-itop-offline.tar.gz \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='instance/*.db' \
    --exclude='logs/*' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    .
```

### محتویات Archive باید شامل:
- تمام فایل‌های Python (app.py, models.py, ...)
- templates/
- static/
- requirements.txt
- Dockerfile و docker-compose.yml
- deploy/ (systemd, nginx configs)
- README.md و این فایل

