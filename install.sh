#!/bin/bash

# اسکریپت نصب خودکار Flask CMS روی Red Hat 8.10
# این اسکریپت تمام وابستگی‌ها را از داخل پروژه نصب می‌کند

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
        log_info "استفاده: sudo ./install.sh"
        exit 1
    fi
}

# بررسی سیستم عامل
check_os() {
    if [[ ! -f /etc/redhat-release ]]; then
        log_error "این اسکریپت فقط برای Red Hat Enterprise Linux طراحی شده است!"
        exit 1
    fi
    
    local version=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+' | head -1)
    log_info "تشخیص سیستم عامل: Red Hat $version"
}

# نصب پکیج‌های سیستم
install_system_packages() {
    log_info "نصب پکیج‌های سیستم..."
    
    # فعال‌سازی repositories
    subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms || true
    subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms || true
    dnf install -y epel-release || true
    
    # نصب گروه Development Tools
    dnf groupinstall -y "Development Tools" || true
    
    # نصب پکیج‌های Python
    dnf install -y python3.11 python3.11-pip python3.11-devel python3.11-setuptools python3.11-wheel
    
    # نصب ابزارهای build
    dnf install -y gcc gcc-c++ make cmake pkg-config
    
    # نصب کتابخانه‌های توسعه
    dnf install -y openssl-devel libffi-devel zlib-devel bzip2-devel readline-devel sqlite-devel
    
    # نصب PostgreSQL
    dnf install -y postgresql15-server postgresql15-devel postgresql15-contrib
    
    # نصب Redis
    dnf install -y redis6 redis6-devel
    
    # نصب Nginx
    dnf install -y nginx
    
    # نصب ابزارهای امنیت
    dnf install -y openssl fail2ban
    
    log_success "پکیج‌های سیستم نصب شدند"
}

# تنظیم PostgreSQL
setup_postgresql() {
    log_info "تنظیم PostgreSQL..."
    
    # راه‌اندازی اولیه
    postgresql-15-setup initdb
    systemctl enable postgresql-15
    systemctl start postgresql-15
    
    # انتظار برای آماده شدن سرویس
    sleep 5
    
    # ایجاد کاربر و دیتابیس
    sudo -u postgres psql << EOF
CREATE USER cms_user WITH PASSWORD 'cms_password';
CREATE DATABASE cms_db OWNER cms_user;
GRANT ALL PRIVILEGES ON DATABASE cms_db TO cms_user;
\q
EOF
    
    # تنظیم pg_hba.conf
    sed -i "s/#local   all             all                                     peer/local   all             all                                     md5/" /var/lib/pgsql/15/data/pg_hba.conf
    systemctl restart postgresql-15
    
    log_success "PostgreSQL تنظیم شد"
}

# تنظیم Redis
setup_redis() {
    log_info "تنظیم Redis..."
    
    systemctl enable redis6
    systemctl start redis6
    
    # تنظیم persistence
    sed -i 's/^# save 900 1/save 900 1/' /etc/redis6.conf
    sed -i 's/^# save 300 10/save 300 10/' /etc/redis6.conf
    sed -i 's/^# save 60 10000/save 60 10000/' /etc/redis6.conf
    systemctl restart redis6
    
    log_success "Redis تنظیم شد"
}

# تنظیم فایروال
setup_firewall() {
    log_info "تنظیم فایروال..."
    
    systemctl enable firewalld
    systemctl start firewalld
    
    # باز کردن پورت‌های مورد نیاز
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --permanent --add-port=5000/tcp
    firewall-cmd --permanent --add-port=5432/tcp
    firewall-cmd --permanent --add-port=6379/tcp
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
    
    # ایجاد دایرکتوری برنامه
    mkdir -p "$PROJECT_DIR"
    
    # کپی فایل‌های برنامه
    cp -r . "$PROJECT_DIR/"
    
    # تنظیم مجوزها
    chown -R "$APP_USER:$APP_USER" "$PROJECT_DIR"
    
    log_success "فایل‌های برنامه کپی شدند"
}

# نصب وابستگی‌های Python
install_python_dependencies() {
    log_info "نصب وابستگی‌های Python..."
    
    # تغییر به کاربر cms
    sudo -u "$APP_USER" bash << EOF
# ایجاد محیط مجازی
python3.11 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# ارتقای pip
pip install --upgrade pip setuptools wheel

# نصب وابستگی‌ها
cd "$PROJECT_DIR"

# اگر فایل requirements-offline.txt وجود دارد، از آن استفاده کن
if [ -f "requirements-offline.txt" ]; then
    pip install -r requirements-offline.txt
else
    pip install -r requirements.txt
fi
EOF
    
    log_success "وابستگی‌های Python نصب شدند"
}

# تنظیم متغیرهای محیطی
setup_environment() {
    log_info "تنظیم متغیرهای محیطی..."
    
    # کپی فایل تنظیمات
    if [ -f "$PROJECT_DIR/production.env" ]; then
        cp "$PROJECT_DIR/production.env" "$PROJECT_DIR/.env"
    else
        log_warning "فایل production.env یافت نشد، از تنظیمات پیش‌فرض استفاده می‌شود"
    fi
    
    # تنظیم مجوزها
    chown "$APP_USER:$APP_USER" "$PROJECT_DIR/.env"
    chmod 600 "$PROJECT_DIR/.env"
    
    log_success "متغیرهای محیطی تنظیم شدند"
}

# تنظیم Nginx
setup_nginx() {
    log_info "تنظیم Nginx..."
    
    # کپی فایل‌های تنظیمات
    if [ -f "$PROJECT_DIR/nginx/nginx.conf" ]; then
        cp "$PROJECT_DIR/nginx/nginx.conf" /etc/nginx/nginx.conf
    fi
    
    if [ -f "$PROJECT_DIR/nginx/conf.d/flask-cms.conf" ]; then
        cp "$PROJECT_DIR/nginx/conf.d/flask-cms.conf" /etc/nginx/conf.d/
    fi
    
    # ایجاد دایرکتوری‌های مورد نیاز
    mkdir -p /var/www/static /var/log/nginx /etc/nginx/ssl
    
    # تنظیم مجوزها
    chown -R nginx:nginx /var/www/static
    chown -R nginx:nginx /var/log/nginx
    
    # تست تنظیمات
    nginx -t
    
    # راه‌اندازی Nginx
    systemctl enable nginx
    systemctl start nginx
    
    log_success "Nginx تنظیم شد"
}

# ایجاد SSL certificate
setup_ssl() {
    log_info "ایجاد SSL certificate..."
    
    if [ ! -f "/etc/nginx/ssl/cert.pem" ] || [ ! -f "/etc/nginx/ssl/key.pem" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout /etc/nginx/ssl/key.pem -out /etc/nginx/ssl/cert.pem -days 365 -nodes -subj "/C=IR/ST=Tehran/L=Tehran/O=CMS/OU=IT/CN=localhost"
        
        # تنظیم مجوزها
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
    
    # انتظار برای آماده شدن سرویس
    sleep 10
    
    # بررسی وضعیت سرویس‌ها
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
    
    # تست health check
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
    echo "   بکاپ دیتابیس: sudo -u postgres pg_dump cms_db > backup.sql"
    echo ""
    echo "🔧 فایل‌های مهم:"
    echo "   تنظیمات برنامه: $PROJECT_DIR/.env"
    echo "   لاگ‌های برنامه: journalctl -u flask-cms"
    echo "   لاگ‌های Nginx: /var/log/nginx/"
    echo "   تنظیمات Nginx: /etc/nginx/conf.d/flask-cms.conf"
    echo ""
}

# تابع اصلی
main() {
    echo "🚀 شروع نصب Flask CMS روی Red Hat 8.10"
    echo "=========================================="
    
    # بررسی‌های اولیه
    check_root
    check_os
    
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



