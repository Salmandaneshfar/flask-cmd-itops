#!/bin/bash

# اسکریپت نصب ساده Flask CMS
# این اسکریپت از پکیج‌های محلی استفاده می‌کند

set -e

# رنگ‌ها برای خروجی
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# توابع کمکی
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# تنظیمات
PROJECT_DIR="/opt/flask-cms"
APP_USER="cms"
VENV_DIR="/home/$APP_USER/venv"

# بررسی root بودن
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "این اسکریپت باید با کاربر root اجرا شود!"
        log_info "استفاده: sudo ./install-simple.sh"
        exit 1
    fi
}

# بررسی وجود فایل‌های مورد نیاز
check_files() {
    log_info "بررسی فایل‌های مورد نیاز..."
    
    local required_files=(
        "app.py"
        "requirements.txt"
        "config.py"
        "models.py"
        "forms.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "فایل $file یافت نشد!"
            exit 1
        fi
    done
    
    log_success "تمام فایل‌های مورد نیاز موجود هستند"
}

# نصب پکیج‌های سیستم
install_system_packages() {
    log_info "نصب پکیج‌های سیستم..."
    
    # فعال‌سازی repositories
    subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms || true
    subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms || true
    dnf install -y epel-release || true
    
    # نصب پکیج‌های اصلی
    dnf install -y python3.11 python3.11-pip python3.11-devel
    dnf install -y gcc gcc-c++ make
    dnf install -y openssl-devel libffi-devel zlib-devel
    dnf install -y postgresql15-server postgresql15-devel
    dnf install -y redis6 redis6-devel
    dnf install -y nginx
    dnf install -y openssl
    
    log_success "پکیج‌های سیستم نصب شدند"
}

# تنظیم PostgreSQL
setup_postgresql() {
    log_info "تنظیم PostgreSQL..."
    
    postgresql-15-setup initdb
    systemctl enable postgresql-15
    systemctl start postgresql-15
    sleep 5
    
    sudo -u postgres psql << EOF
CREATE USER cms_user WITH PASSWORD 'cms_password';
CREATE DATABASE cms_db OWNER cms_user;
GRANT ALL PRIVILEGES ON DATABASE cms_db TO cms_user;
\q
EOF
    
    sed -i "s/#local   all             all                                     peer/local   all             all                                     md5/" /var/lib/pgsql/15/data/pg_hba.conf
    systemctl restart postgresql-15
    
    log_success "PostgreSQL تنظیم شد"
}

# تنظیم Redis
setup_redis() {
    log_info "تنظیم Redis..."
    
    systemctl enable redis6
    systemctl start redis6
    sed -i 's/^# save 900 1/save 900 1/' /etc/redis6.conf
    systemctl restart redis6
    
    log_success "Redis تنظیم شد"
}

# تنظیم فایروال
setup_firewall() {
    log_info "تنظیم فایروال..."
    
    systemctl enable firewalld
    systemctl start firewalld
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --permanent --add-port=5000/tcp
    firewall-cmd --reload
    
    log_success "فایروال تنظیم شد"
}

# ایجاد کاربر برنامه
create_app_user() {
    log_info "ایجاد کاربر برنامه..."
    
    if ! id "$APP_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$APP_USER"
        usermod -aG wheel "$APP_USER"
        log_success "کاربر $APP_USER ایجاد شد"
    else
        log_info "کاربر $APP_USER از قبل موجود است"
    fi
}

# کپی فایل‌های برنامه
copy_application_files() {
    log_info "کپی فایل‌های برنامه..."
    
    mkdir -p "$PROJECT_DIR"
    cp -r . "$PROJECT_DIR/"
    chown -R "$APP_USER:$APP_USER" "$PROJECT_DIR"
    
    log_success "فایل‌های برنامه کپی شدند"
}

# نصب وابستگی‌های Python
install_python_dependencies() {
    log_info "نصب وابستگی‌های Python..."
    
    # اگر دایرکتوری python-packages وجود دارد، از آن استفاده کن
    if [ -d "python-packages" ]; then
        log_info "استفاده از پکیج‌های محلی..."
        sudo -u "$APP_USER" bash << EOF
python3.11 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
cd "$PROJECT_DIR"
pip install --no-index --find-links python-packages -r requirements.txt
EOF
    else
        log_info "دانلود پکیج‌ها از اینترنت..."
        sudo -u "$APP_USER" bash << EOF
python3.11 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
cd "$PROJECT_DIR"
pip install -r requirements.txt
EOF
    fi
    
    log_success "وابستگی‌های Python نصب شدند"
}

# تنظیم متغیرهای محیطی
setup_environment() {
    log_info "تنظیم متغیرهای محیطی..."
    
    if [ -f "$PROJECT_DIR/production.env" ]; then
        cp "$PROJECT_DIR/production.env" "$PROJECT_DIR/.env"
    fi
    
    chown "$APP_USER:$APP_USER" "$PROJECT_DIR/.env"
    chmod 600 "$PROJECT_DIR/.env"
    
    log_success "متغیرهای محیطی تنظیم شدند"
}

# تنظیم Nginx
setup_nginx() {
    log_info "تنظیم Nginx..."
    
    if [ -f "$PROJECT_DIR/nginx/nginx.conf" ]; then
        cp "$PROJECT_DIR/nginx/nginx.conf" /etc/nginx/nginx.conf
    fi
    
    if [ -f "$PROJECT_DIR/nginx/conf.d/flask-cms.conf" ]; then
        cp "$PROJECT_DIR/nginx/conf.d/flask-cms.conf" /etc/nginx/conf.d/
    fi
    
    mkdir -p /var/www/static /var/log/nginx /etc/nginx/ssl
    chown -R nginx:nginx /var/www/static
    chown -R nginx:nginx /var/log/nginx
    
    nginx -t
    systemctl enable nginx
    systemctl start nginx
    
    log_success "Nginx تنظیم شد"
}

# ایجاد SSL certificate
setup_ssl() {
    log_info "ایجاد SSL certificate..."
    
    if [ ! -f "/etc/nginx/ssl/cert.pem" ] || [ ! -f "/etc/nginx/ssl/key.pem" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout /etc/nginx/ssl/key.pem -out /etc/nginx/ssl/cert.pem -days 365 -nodes -subj "/C=IR/ST=Tehran/L=Tehran/O=CMS/OU=IT/CN=localhost"
        chmod 600 /etc/nginx/ssl/key.pem
        chmod 644 /etc/nginx/ssl/cert.pem
        chown root:root /etc/nginx/ssl/*
        log_success "SSL certificate ایجاد شد"
    else
        log_info "SSL certificate از قبل موجود است"
    fi
}

# ایجاد systemd service
create_systemd_service() {
    log_info "ایجاد systemd service..."
    
    tee /etc/systemd/system/flask-cms.service > /dev/null << EOF
[Unit]
Description=Flask CMS Application
After=network.target postgresql-15.service redis6.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 120 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable flask-cms
    
    log_success "systemd service ایجاد شد"
}

# راه‌اندازی اولیه دیتابیس
init_database() {
    log_info "راه‌اندازی اولیه دیتابیس..."
    
    sudo -u "$APP_USER" bash << EOF
source "$VENV_DIR/bin/activate"
cd "$PROJECT_DIR"
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ دیتابیس راه‌اندازی شد')"
EOF
    
    log_success "دیتابیس راه‌اندازی شد"
}

# راه‌اندازی سرویس‌ها
start_services() {
    log_info "راه‌اندازی سرویس‌ها..."
    
    systemctl start flask-cms
    sleep 10
    
    log_info "بررسی وضعیت سرویس‌ها..."
    systemctl status flask-cms --no-pager -l
    systemctl status postgresql-15 --no-pager -l
    systemctl status redis6 --no-pager -l
    systemctl status nginx --no-pager -l
    
    log_success "سرویس‌ها راه‌اندازی شدند"
}

# تست نصب
test_installation() {
    log_info "تست نصب..."
    
    for i in {1..10}; do
        if curl -f http://localhost/health > /dev/null 2>&1; then
            log_success "برنامه با موفقیت راه‌اندازی شد!"
            break
        else
            log_info "انتظار برای آماده شدن برنامه... ($i/10)"
            sleep 10
        fi
    done
    
    if [ $i -eq 10 ]; then
        log_error "برنامه پس از 100 ثانیه آماده نشد!"
        log_info "لطفاً لاگ‌ها را بررسی کنید: journalctl -u flask-cms -f"
        return 1
    fi
}

# نمایش اطلاعات نهایی
show_final_info() {
    echo ""
    echo "🎉 نصب Flask CMS با موفقیت تکمیل شد!"
    echo ""
    echo "📊 اطلاعات دسترسی:"
    echo "   🌐 وب سایت: http://localhost"
    echo "   📊 Health Check: http://localhost/health"
    echo ""
    echo "👤 اطلاعات ورود پیش‌فرض:"
    echo "   نام کاربری: admin"
    echo "   رمز عبور: admin123"
    echo ""
    echo "📋 دستورات مفید:"
    echo "   مشاهده وضعیت: systemctl status flask-cms"
    echo "   مشاهده لاگ‌ها: journalctl -u flask-cms -f"
    echo "   متوقف کردن: systemctl stop flask-cms"
    echo "   راه‌اندازی مجدد: systemctl restart flask-cms"
    echo ""
}

# تابع اصلی
main() {
    echo "🚀 شروع نصب Flask CMS روی Red Hat 8.10"
    echo "=========================================="
    
    # بررسی‌های اولیه
    check_root
    check_files
    
    # تایید نصب
    echo ""
    log_warning "این اسکریپت موارد زیر را نصب و تنظیم خواهد کرد:"
    echo "  - Python 3.11 و وابستگی‌ها"
    echo "  - PostgreSQL 15"
    echo "  - Redis 6"
    echo "  - Nginx"
    echo "  - Flask CMS Application"
    echo ""
    read -p "آیا می‌خواهید ادامه دهید؟ (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "نصب لغو شد."
        exit 0
    fi
    
    # مراحل نصب
    install_system_packages
    setup_postgresql
    setup_redis
    setup_firewall
    create_app_user
    copy_application_files
    install_python_dependencies
    setup_environment
    setup_nginx
    setup_ssl
    create_systemd_service
    init_database
    start_services
    test_installation
    show_final_info
}

# اجرای تابع اصلی
main "$@"



