#!/bin/bash

echo "=== نصب بسته‌های FreeIPA ==="

# رنگ‌ها برای نمایش بهتر
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[مرحله $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# مرحله 1: بررسی سیستم
print_step "1" "بررسی سیستم..."
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Architecture: $(uname -m)"
echo ""

# مرحله 2: حذف بسته‌های قبلی
print_step "2" "حذف بسته‌های قبلی..."
dnf remove -y ipa-server ipa-server-dns pki-ca pki-tomcat 2>/dev/null || true
print_success "بسته‌های قبلی حذف شدند"

# مرحله 3: پاک کردن cache
print_step "3" "پاک کردن cache..."
dnf clean all
print_success "Cache پاک شد"

# مرحله 4: به‌روزرسانی سیستم
print_step "4" "به‌روزرسانی سیستم..."
dnf update -y
print_success "سیستم به‌روزرسانی شد"

# مرحله 5: نصب EPEL
print_step "5" "نصب EPEL..."
dnf install -y epel-release
print_success "EPEL نصب شد"

# مرحله 6: نصب بسته‌های مورد نیاز
print_step "6" "نصب بسته‌های مورد نیاز..."
dnf install -y bind bind-dyndb-ldap
print_success "بسته‌های DNS نصب شدند"

# مرحله 7: نصب FreeIPA
print_step "7" "نصب FreeIPA..."
dnf install -y ipa-server ipa-server-dns
print_success "بسته‌های FreeIPA نصب شدند"

# مرحله 8: بررسی نصب
print_step "8" "بررسی نصب..."
echo "=== بسته‌های FreeIPA نصب شده ==="
rpm -qa | grep ipa
echo ""

# مرحله 9: بررسی فایل‌های اجرایی
print_step "9" "بررسی فایل‌های اجرایی..."
echo "=== بررسی ipa-server-install ==="
which ipa-server-install
ls -la /usr/sbin/ipa-server-install 2>/dev/null || echo "فایل ipa-server-install یافت نشد"
echo ""

# مرحله 10: بررسی سایر فایل‌های مهم
print_step "10" "بررسی سایر فایل‌های مهم..."
echo "=== فایل‌های اجرایی FreeIPA ==="
ls -la /usr/sbin/ipa-* 2>/dev/null | head -10
echo ""

# مرحله 11: تست دستور
print_step "11" "تست دستور ipa-server-install..."
if [ -f "/usr/sbin/ipa-server-install" ]; then
    print_success "فایل ipa-server-install موجود است"
    echo "=== کمک دستور ==="
    /usr/sbin/ipa-server-install --help | head -20
else
    print_error "فایل ipa-server-install یافت نشد!"
    echo "لطفاً بسته‌های FreeIPA را دوباره نصب کنید"
fi

echo ""
echo "=========================================="
print_success "نصب بسته‌های FreeIPA تکمیل شد!"
echo "=========================================="
echo "حالا می‌توانید FreeIPA را نصب کنید:"
echo "sudo ipa-server-install --help"
echo "=========================================="
