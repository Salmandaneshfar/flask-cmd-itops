# چک‌لیست نصب آفلاین - Flask CMS iTop

## فایل‌های آماده شده

### 1. پکیج ساده (بدون dependencies)
- **فایل**: `flask-cms-itop-simple-*.tar.gz`
- **حجم**: ~2-3 MB
- **استفاده**: انتقال سریع فایل‌های پروژه
- **نکته**: نیاز به اینترنت برای نصب dependencies در سرور

### 2. پکیج کامل (با wheel files)
- **فایل**: `flask-cms-itop-offline-*.tar.gz` (در حال ساخت)
- **حجم**: ~100-200 MB (بسته به dependencies)
- **استفاده**: نصب کاملاً آفلاین
- **نکته**: زمان ساخت بیشتر اما نصب سریع‌تر

### 3. Docker Images
- **فایل**: `flask-cms-itop-docker-images-*.tar`
- **حجم**: ~500-1000 MB
- **استفاده**: نصب با Docker (توصیه می‌شود)
- **نکته**: نیاز به Docker در سرور

## مراحل نصب در سرور آفلاین

### روش 1: با Python venv (پکیج ساده)

```bash
# 1. انتقال فایل
scp flask-cms-itop-simple-*.tar.gz user@server:/opt/

# 2. در سرور
cd /opt
tar -xzf flask-cms-itop-simple-*.tar.gz
cd flask-cms-itop

# 3. نصب Python و dependencies
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt  # نیاز به اینترنت!

# 4. ساخت .env
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
CREDENTIALS_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
cat > .env <<EOF
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY
CREDENTIALS_KEY=$CREDENTIALS_KEY
UPLOAD_FOLDER=static/uploads
DATABASE_URL=sqlite:///instance/cms.db
EOF

# 5. راه‌اندازی دیتابیس
mkdir -p instance static/uploads logs
flask db upgrade

# 6. ساخت admin user
python <<EOF
from app import create_app, db
from models import User
app = create_app('production')
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin', is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin created: admin / admin123")
EOF

# 7. اجرا با Gunicorn
gunicorn -c gunicorn.conf.py wsgi:application
```

### روش 2: با Python venv (پکیج کامل با wheels)

```bash
# 1. انتقال فایل
scp flask-cms-itop-offline-*.tar.gz user@server:/opt/

# 2. در سرور
cd /opt
tar -xzf flask-cms-itop-offline-*.tar.gz
cd flask-cms-itop-offline

# 3. اجرای اسکریپت نصب
chmod +x install_offline.sh
./install_offline.sh

# 4. ساخت admin user (مانند روش 1)
# 5. اجرا با Gunicorn
```

### روش 3: با Docker (توصیه می‌شود)

```bash
# 1. در محیط با اینترنت - ساخت images
./prepare_docker_offline.sh

# 2. انتقال فایل‌ها به سرور
scp flask-cms-itop-docker-images-*.tar user@server:/opt/
scp -r docker-compose.yml Dockerfile docker/ user@server:/opt/flask-cms-itop/

# 3. در سرور
cd /opt/flask-cms-itop
docker load < flask-cms-itop-docker-images-*.tar

# 4. ساخت .env.docker
cp docker/env.docker.sample .env.docker
# ویرایش .env.docker و تولید SECRET_KEY و CREDENTIALS_KEY

# 5. اجرا
docker compose up -d
```

## چک‌لیست قبل از انتقال

- [ ] فایل tar.gz ساخته شده
- [ ] فایل‌های حساس (.env) در archive نیستند
- [ ] دیتابیس (instance/*.db) در archive نیست
- [ ] .venv در archive نیست
- [ ] فایل README و OFFLINE_DEPLOYMENT.md موجود است

## چک‌لیست در سرور

- [ ] Python 3.11+ نصب است
- [ ] pip و venv در دسترس است
- [ ] یا Docker و Docker Compose نصب است
- [ ] پورت 8000 یا 80 آزاد است
- [ ] دسترسی نوشتن در دایرکتوری پروژه وجود دارد

## عیب‌یابی

### مشکل: ModuleNotFoundError
```bash
# بررسی نصب پکیج‌ها
pip list | grep <package_name>
pip install <package_name>
```

### مشکل: Database locked
```bash
# بررسی process های در حال استفاده
lsof instance/cms.db
# یا restart
sudo systemctl restart flask-cms-itop
```

### مشکل: Permission denied
```bash
# تنظیم دسترسی‌ها
sudo chown -R user:user /opt/flask-cms-itop
sudo chmod -R 755 /opt/flask-cms-itop
```

