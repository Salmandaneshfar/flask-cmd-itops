#!/bin/bash

# اسکریپت نصب Flask CMS روی Red Hat 8.10
# استفاده: ./install-redhat.sh

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

# بررسی root بودن
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "این اسکریپت نباید با کاربر root اجرا شود!"
        log_info "لطفاً با کاربر عادی اجرا کنید. اسکریپت در صورت نیاز از sudo استفاده خواهد کرد."
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
    
    if [[ "$version" != "8.10" ]]; then
        log_warning "این اسکریپت برای RHEL 8.10 طراحی شده است. نسخه فعلی: $version"
        read -p "آیا می‌خواهید ادامه دهید؟ (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# نصب پکیج‌های سیستم
install_system_packages() {
    log_info "نصب پکیج‌های سیستم..."
    
    # فعال‌سازی repositories
    sudo subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms
    sudo subscription-manager repos --enable=rhel-8-for-x86_64-baseos-rpms
    sudo dnf install -y epel-release
    
    # نصب گروه Development Tools
    sudo dnf groupinstall -y "Development Tools"
    
    # نصب پکیج‌های Python
    sudo dnf install -y python3.11 python3.11-pip python3.11-devel python3.11-setuptools python3.11-wheel
    
    # نصب ابزارهای build
    sudo dnf install -y gcc gcc-c++ make cmake pkg-config
    
    # نصب کتابخانه‌های توسعه
    sudo dnf install -y openssl-devel libffi-devel zlib-devel bzip2-devel readline-devel sqlite-devel
    
    # نصب PostgreSQL
    sudo dnf install -y postgresql15-server postgresql15-devel postgresql15-contrib
    
    # نصب Redis
    sudo dnf install -y redis6 redis6-devel
    
    # نصب Nginx
    sudo dnf install -y nginx
    
    # نصب ابزارهای امنیت
    sudo dnf install -y openssl fail2ban
    
    log_success "پکیج‌های سیستم با موفقیت نصب شدند"
}

# تنظیم PostgreSQL
setup_postgresql() {
    log_info "تنظیم PostgreSQL..."
    
    # راه‌اندازی اولیه
    sudo postgresql-15-setup initdb
    sudo systemctl enable postgresql-15
    sudo systemctl start postgresql-15
    
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
    sudo sed -i "s/#local   all             all                                     peer/local   all             all                                     md5/" /var/lib/pgsql/15/data/pg_hba.conf
    sudo systemctl restart postgresql-15
    
    log_success "PostgreSQL تنظیم شد"
}

# تنظیم Redis
setup_redis() {
    log_info "تنظیم Redis..."
    
    sudo systemctl enable redis6
    sudo systemctl start redis6
    
    # تنظیم persistence
    sudo sed -i 's/^# save 900 1/save 900 1/' /etc/redis6.conf
    sudo sed -i 's/^# save 300 10/save 300 10/' /etc/redis6.conf
    sudo sed -i 's/^# save 60 10000/save 60 10000/' /etc/redis6.conf
    sudo systemctl restart redis6
    
    log_success "Redis تنظیم شد"
}

# تنظیم فایروال
setup_firewall() {
    log_info "تنظیم فایروال..."
    
    sudo systemctl enable firewalld
    sudo systemctl start firewalld
    
    # باز کردن پورت‌های مورد نیاز
    sudo firewall-cmd --permanent --add-port=80/tcp
    sudo firewall-cmd --permanent --add-port=443/tcp
    sudo firewall-cmd --permanent --add-port=5000/tcp
    sudo firewall-cmd --permanent --add-port=5432/tcp
    sudo firewall-cmd --permanent --add-port=6379/tcp
    sudo firewall-cmd --reload
    
    log_success "فایروال تنظیم شد"
}

# ایجاد کاربر برنامه
create_app_user() {
    log_info "ایجاد کاربر برنامه..."
    
    if ! id "cms" &>/dev/null; then
        sudo useradd -m -s /bin/bash cms
        sudo usermod -aG wheel cms
        log_success "کاربر cms ایجاد شد"
    else
        log_info "کاربر cms از قبل موجود است"
    fi
}

# نصب Python و وابستگی‌ها
setup_python() {
    log_info "تنظیم Python و وابستگی‌ها..."
    
    # تغییر به کاربر cms
    sudo su - cms << 'EOF'
# ایجاد محیط مجازی
python3.11 -m venv /home/cms/venv
source /home/cms/venv/bin/activate

# ارتقای pip
pip install --upgrade pip setuptools wheel

# نصب وابستگی‌ها
if [ -f "/opt/flask-cms/requirements-offline.txt" ]; then
    pip install --no-index --find-links /opt/flask-cms/offline-packages -r /opt/flask-cms/requirements-offline.txt
else
    pip install -r /opt/flask-cms/requirements.txt
fi
EOF
    
    log_success "Python و وابستگی‌ها تنظیم شدند"
}

# تنظیم Nginx
setup_nginx() {
    log_info "تنظیم Nginx..."
    
    # کپی فایل‌های تنظیمات
    if [ -f "/opt/flask-cms/nginx/nginx.conf" ]; then
        sudo cp /opt/flask-cms/nginx/nginx.conf /etc/nginx/nginx.conf
    fi
    
    if [ -f "/opt/flask-cms/nginx/conf.d/flask-cms.conf" ]; then
        sudo cp /opt/flask-cms/nginx/conf.d/flask-cms.conf /etc/nginx/conf.d/
    fi
    
    # ایجاد دایرکتوری‌های مورد نیاز
    sudo mkdir -p /var/www/static /var/log/nginx /etc/nginx/ssl
    
    # تنظیم مجوزها
    sudo chown -R nginx:nginx /var/www/static
    sudo chown -R nginx:nginx /var/log/nginx
    
    # تست تنظیمات
    sudo nginx -t
    
    # راه‌اندازی Nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx
    
    log_success "Nginx تنظیم شد"
}

# ایجاد SSL certificate
setup_ssl() {
    log_info "ایجاد SSL certificate..."
    
    if [ ! -f "/etc/nginx/ssl/cert.pem" ] || [ ! -f "/etc/nginx/ssl/key.pem" ]; then
        sudo openssl req -x509 -newkey rsa:4096 -keyout /etc/nginx/ssl/key.pem -out /etc/nginx/ssl/cert.pem -days 365 -nodes -subj "/C=IR/ST=Tehran/L=Tehran/O=CMS/OU=IT/CN=localhost"
        
        # تنظیم مجوزها
        sudo chmod 600 /etc/nginx/ssl/key.pem
        sudo chmod 644 /etc/nginx/ssl/cert.pem
        sudo chown root:root /etc/nginx/ssl/*
        
        log_success "SSL certificate ایجاد شد"
    else
        log_info "SSL certificate از قبل موجود است"
    fi
}

# ایجاد systemd service
create_systemd_service() {
    log_info "ایجاد systemd service..."
    
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
    
    sudo systemctl daemon-reload
    sudo systemctl enable flask-cms
    
    log_success "systemd service ایجاد شد"
}

# راه‌اندازی اولیه دیتابیس
init_database() {
    log_info "راه‌اندازی اولیه دیتابیس..."
    
    sudo su - cms << 'EOF'
source /home/cms/venv/bin/activate
cd /opt/flask-cms
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ دیتابیس راه‌اندازی شد')"
EOF
    
    log_success "دیتابیس راه‌اندازی شد"
}

# راه‌اندازی سرویس‌ها
start_services() {
    log_info "راه‌اندازی سرویس‌ها..."
    
    sudo systemctl start flask-cms
    
    # انتظار برای آماده شدن سرویس
    sleep 10
    
    # بررسی وضعیت سرویس‌ها
    log_info "بررسی وضعیت سرویس‌ها..."
    sudo systemctl status flask-cms --no-pager -l
    sudo systemctl status postgresql-15 --no-pager -l
    sudo systemctl status redis6 --no-pager -l
    sudo systemctl status nginx --no-pager -l
    
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
        log_info "لطفاً لاگ‌ها را بررسی کنید: sudo journalctl -u flask-cms -f"
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
    echo "   مشاهده وضعیت: sudo systemctl status flask-cms"
    echo "   مشاهده لاگ‌ها: sudo journalctl -u flask-cms -f"
    echo "   متوقف کردن: sudo systemctl stop flask-cms"
    echo "   راه‌اندازی مجدد: sudo systemctl restart flask-cms"
    echo "   بکاپ دیتابیس: sudo -u postgres pg_dump cms_db > backup.sql"
    echo ""
    echo "🔧 فایل‌های مهم:"
    echo "   تنظیمات برنامه: /opt/flask-cms/.env"
    echo "   لاگ‌های برنامه: sudo journalctl -u flask-cms"
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
    setup_python
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

