#!/bin/bash

# اسکریپت بسته‌بندی وابستگی‌های Python برای نصب آفلاین
# این اسکریپت تمام وابستگی‌ها را دانلود و در پروژه قرار می‌دهد

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
PACKAGES_DIR="python-packages"
REQUIREMENTS_FILE="requirements.txt"

# بررسی وجود فایل requirements
check_requirements() {
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        log_error "فایل $REQUIREMENTS_FILE یافت نشد!"
        exit 1
    fi
    log_success "فایل $REQUIREMENTS_FILE یافت شد"
}

# ایجاد دایرکتوری پکیج‌ها
create_packages_directory() {
    log_info "ایجاد دایرکتوری پکیج‌ها..."
    
    if [ -d "$PACKAGES_DIR" ]; then
        log_warning "دایرکتوری $PACKAGES_DIR از قبل موجود است. حذف می‌شود..."
        rm -rf "$PACKAGES_DIR"
    fi
    
    mkdir -p "$PACKAGES_DIR"
    log_success "دایرکتوری $PACKAGES_DIR ایجاد شد"
}

# دانلود پکیج‌های Python
download_python_packages() {
    log_info "دانلود پکیج‌های Python..."
    
    # ایجاد محیط مجازی موقت
    python3 -m venv temp_venv
    source temp_venv/bin/activate
    
    # ارتقای pip
    pip install --upgrade pip setuptools wheel
    
    # دانلود پکیج‌ها
    cd "$PACKAGES_DIR"
    pip download -r "../$REQUIREMENTS_FILE"
    cd ..
    
    # حذف محیط مجازی موقت
    deactivate
    rm -rf temp_venv
    
    log_success "پکیج‌های Python دانلود شدند"
}

# ایجاد فایل نصب پکیج‌ها
create_install_script() {
    log_info "ایجاد اسکریپت نصب پکیج‌ها..."
    
    cat > "install-packages.sh" << 'EOF'
#!/bin/bash

# اسکریپت نصب پکیج‌های Python از دایرکتوری محلی
# این اسکریپت توسط bundle-dependencies.sh ایجاد شده است

set -e

PACKAGES_DIR="python-packages"

if [ ! -d "$PACKAGES_DIR" ]; then
    echo "خطا: دایرکتوری $PACKAGES_DIR یافت نشد!"
    exit 1
fi

echo "نصب پکیج‌های Python از دایرکتوری محلی..."
cd "$PACKAGES_DIR"

# نصب تمام فایل‌های wheel و tar.gz
pip install --no-index --find-links . *.whl *.tar.gz

echo "پکیج‌های Python با موفقیت نصب شدند"
EOF
    
    chmod +x install-packages.sh
    log_success "اسکریپت install-packages.sh ایجاد شد"
}

# ایجاد فایل requirements آفلاین
create_offline_requirements() {
    log_info "ایجاد فایل requirements آفلاین..."
    
    # کپی فایل requirements اصلی
    cp "$REQUIREMENTS_FILE" "requirements-offline.txt"
    
    # اضافه کردن کامنت
    cat > temp_requirements.txt << EOF
# Flask CMS - Requirements for Offline Installation
# این فایل برای نصب آفلاین استفاده می‌شود
# تمام پکیج‌ها در دایرکتوری python-packages موجود هستند

EOF
    
    cat "$REQUIREMENTS_FILE" >> temp_requirements.txt
    mv temp_requirements.txt "requirements-offline.txt"
    
    log_success "فایل requirements-offline.txt ایجاد شد"
}

# ایجاد فایل README
create_readme() {
    log_info "ایجاد فایل README..."
    
    cat > "README-BUNDLE.md" << EOF
# Flask CMS - بسته‌بندی شده برای نصب آفلاین

## 📦 محتویات

این پروژه شامل تمام وابستگی‌های مورد نیاز برای نصب آفلاین است:

- \`python-packages/\` - تمام پکیج‌های Python
- \`requirements-offline.txt\` - لیست وابستگی‌ها
- \`install-packages.sh\` - اسکریپت نصب پکیج‌ها
- \`install.sh\` - اسکریپت نصب کامل

## 🚀 نحوه نصب

### روی سرور Red Hat 8.10:

\`\`\`bash
# 1. کپی پروژه به سرور
scp -r flask-cms-itop/ user@server:/tmp/

# 2. نصب کامل
cd /tmp/flask-cms-itop
sudo ./install.sh
\`\`\`

### نصب دستی پکیج‌های Python:

\`\`\`bash
# نصب پکیج‌های Python
./install-packages.sh

# یا نصب دستی
cd python-packages
pip install --no-index --find-links . *.whl *.tar.gz
\`\`\`

## 📋 پیش‌نیازها

- Red Hat Enterprise Linux 8.10
- دسترسی sudo
- اتصال اینترنت (فقط برای نصب پکیج‌های سیستم)

## 🔧 تنظیمات

پس از نصب، برنامه در آدرس زیر در دسترس خواهد بود:
- **وب سایت:** http://localhost
- **نام کاربری:** admin
- **رمز عبور:** admin123

## 📞 پشتیبانی

برای گزارش مشکل یا درخواست کمک، لاگ‌های سیستم را بررسی کنید:
- \`journalctl -u flask-cms -f\`
- \`/var/log/nginx/error.log\`

---
**توسعه داده شده با ❤️ برای نصب آفلاین**
EOF
    
    log_success "فایل README-BUNDLE.md ایجاد شد"
}

# نمایش آمار
show_stats() {
    echo ""
    echo "📊 آمار بسته‌بندی:"
    echo "   📦 تعداد فایل‌های Python: $(find "$PACKAGES_DIR" -name "*.whl" -o -name "*.tar.gz" | wc -l)"
    echo "   💾 اندازه دایرکتوری پکیج‌ها: $(du -sh "$PACKAGES_DIR" | cut -f1)"
    echo "   📋 تعداد وابستگی‌ها: $(wc -l < "$REQUIREMENTS_FILE")"
    echo ""
}

# نمایش اطلاعات نهایی
show_final_info() {
    echo ""
    echo "🎉 بسته‌بندی وابستگی‌ها با موفقیت تکمیل شد!"
    echo ""
    echo "📁 فایل‌های ایجاد شده:"
    echo "   📦 دایرکتوری پکیج‌ها: $PACKAGES_DIR/"
    echo "   📋 فایل requirements آفلاین: requirements-offline.txt"
    echo "   🔧 اسکریپت نصب پکیج‌ها: install-packages.sh"
    echo "   📖 راهنما: README-BUNDLE.md"
    echo ""
    echo "🚀 مراحل بعدی:"
    echo "   1. کپی کل پروژه به سرور مقصد"
    echo "   2. اجرای sudo ./install.sh روی سرور"
    echo "   3. یا نصب دستی با ./install-packages.sh"
    echo ""
}

# تابع اصلی
main() {
    echo "📦 شروع بسته‌بندی وابستگی‌های Flask CMS"
    echo "======================================"
    
    # بررسی‌های اولیه
    check_requirements
    
    # تایید بسته‌بندی
    echo ""
    log_warning "این اسکریپت موارد زیر را انجام خواهد داد:"
    echo "  - دانلود تمام وابستگی‌های Python"
    echo "  - ایجاد دایرکتوری python-packages"
    echo "  - ایجاد اسکریپت‌های نصب"
    echo ""
    read -p "آیا می‌خواهید ادامه دهید؟ (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "بسته‌بندی لغو شد."
        exit 0
    fi
    
    # مراحل بسته‌بندی
    create_packages_directory
    download_python_packages
    create_install_script
    create_offline_requirements
    create_readme
    show_stats
    show_final_info
}

# اجرای تابع اصلی
main "$@"



