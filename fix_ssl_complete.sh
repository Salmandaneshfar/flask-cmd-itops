#!/bin/bash

echo "=== حل کامل مشکل SSL ==="

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

# مرحله 2: بررسی فایل‌های certificate
print_step "2" "بررسی فایل‌های certificate..."
echo "=== بررسی فایل‌های certificate ==="
ls -la /etc/pki/tls/certs/ca-bundle.crt
ls -la /etc/pki/tls/certs/ca-bundle.trust.crt
echo ""

# مرحله 3: حل مشکل SSL
print_step "3" "حل مشکل SSL..."
# به‌روزرسانی certificate ها
dnf update -y ca-certificates
# نصب certificate های جدید
dnf install -y ca-certificates
# به‌روزرسانی certificate bundle
update-ca-trust
print_success "Certificate ها به‌روزرسانی شدند"

# مرحله 4: پاک کردن cache
print_step "4" "پاک کردن cache..."
dnf clean all
rm -rf /var/cache/dnf
print_success "Cache پاک شد"

# مرحله 5: تنظیم repository ها
print_step "5" "تنظیم repository ها..."
# حذف repository های تکراری
rm -f /etc/yum.repos.d/rocky-*.repo
# نصب repository های جدید
dnf install -y rocky-release
print_success "Repository ها تنظیم شدند"

# مرحله 6: تنظیم SSL برای dnf
print_step "6" "تنظیم SSL برای dnf..."
# غیرفعال کردن SSL verification موقت
echo "sslverify=false" >> /etc/dnf/dnf.conf
print_success "SSL verification غیرفعال شد"

# مرحله 7: به‌روزرسانی سیستم
print_step "7" "به‌روزرسانی سیستم..."
dnf update -y
print_success "سیستم به‌روزرسانی شد"

# مرحله 8: نصب EPEL
print_step "8" "نصب EPEL..."
dnf install -y epel-release
print_success "EPEL نصب شد"

# مرحله 9: نصب بسته‌های مورد نیاز
print_step "9" "نصب بسته‌های مورد نیاز..."
dnf install -y bind bind-dyndb-ldap
print_success "بسته‌های DNS نصب شدند"

# مرحله 10: نصب FreeIPA
print_step "10" "نصب FreeIPA..."
dnf install -y freeipa-server freeipa-server-dns
print_success "بسته‌های FreeIPA نصب شدند"

# مرحله 11: فعال کردن مجدد SSL verification
print_step "11" "فعال کردن مجدد SSL verification..."
# حذف خط sslverify=false
sed -i '/sslverify=false/d' /etc/dnf/dnf.conf
print_success "SSL verification فعال شد"

# مرحله 12: بررسی نصب
print_step "12" "بررسی نصب..."
echo "=== بسته‌های FreeIPA نصب شده ==="
rpm -qa | grep -E "(ipa|freeipa)" | sort
echo ""

# مرحله 13: بررسی فایل‌های اجرایی
print_step "13" "بررسی فایل‌های اجرایی..."
echo "=== جستجوی ipa-server-install ==="
find /usr -name "ipa-server-install" 2>/dev/null
echo ""

# مرحله 14: بررسی مسیرهای مختلف
print_step "14" "بررسی مسیرهای مختلف..."
echo "=== فایل‌های اجرایی FreeIPA ==="
find /usr -name "ipa-*" -type f -executable 2>/dev/null | head -10
echo ""

# مرحله 15: تست دستور
print_step "15" "تست دستور ipa-server-install..."
if command -v ipa-server-install >/dev/null 2>&1; then
    print_success "دستور ipa-server-install یافت شد"
    echo "=== کمک دستور ==="
    ipa-server-install --help | head -20
elif [ -f "/usr/sbin/ipa-server-install" ]; then
    print_success "فایل ipa-server-install در /usr/sbin یافت شد"
    echo "=== کمک دستور ==="
    /usr/sbin/ipa-server-install --help | head -20
elif [ -f "/usr/bin/ipa-server-install" ]; then
    print_success "فایل ipa-server-install در /usr/bin یافت شد"
    echo "=== کمک دستور ==="
    /usr/bin/ipa-server-install --help | head -20
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
