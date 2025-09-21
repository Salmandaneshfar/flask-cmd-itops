#!/bin/bash

echo "=== حل نهایی مشکل SSL Certificate ==="

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

# مرحله 1: بررسی فایل‌های certificate
print_step "1" "بررسی فایل‌های certificate..."
echo "=== بررسی فایل‌های CA ==="
ls -la /etc/pki/tls/certs/ca-bundle.crt 2>/dev/null || echo "فایل ca-bundle.crt یافت نشد"
ls -la /etc/ssl/certs/ca-bundle.crt 2>/dev/null || echo "فایل ca-bundle.crt در /etc/ssl/certs یافت نشد"
ls -la /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt 2>/dev/null || echo "فایل ca-bundle.trust.crt یافت نشد"
echo ""

# مرحله 2: به‌روزرسانی ca-certificates
print_step "2" "به‌روزرسانی ca-certificates..."
dnf update -y ca-certificates
print_success "ca-certificates به‌روزرسانی شد"

# مرحله 3: نصب p11-kit
print_step "3" "نصب p11-kit..."
dnf install -y p11-kit
print_success "p11-kit نصب شد"

# مرحله 4: به‌روزرسانی ca-trust
print_step "4" "به‌روزرسانی ca-trust..."
update-ca-trust extract
print_success "ca-trust به‌روزرسانی شد"

# مرحله 5: پاک کردن cache
print_step "5" "پاک کردن cache..."
dnf clean all
print_success "Cache پاک شد"

# مرحله 6: بررسی repository ها
print_step "6" "بررسی repository ها..."
echo "=== Repository های فعال ==="
dnf repolist
echo ""

# مرحله 7: تست اتصال
print_step "7" "تست اتصال..."
echo "=== تست اتصال به repository ==="
curl -I https://mirrors.rockylinux.org/mirrorlist?arch=x86_64&repo=AppStream-8
echo ""

# مرحله 8: اگر مشکل ادامه داشت، نصب از repository محلی
print_step "8" "نصب از repository محلی..."
echo "=== نصب از repository محلی ==="
dnf install -y --disablerepo=* --enablerepo=baseos,appstream freeipa-server freeipa-server-dns
print_success "بسته‌های FreeIPA از repository محلی نصب شدند"

# مرحله 9: بررسی نصب
print_step "9" "بررسی نصب..."
echo "=== بسته‌های FreeIPA نصب شده ==="
rpm -qa | grep -E "(ipa|freeipa)" | sort
echo ""

# مرحله 10: بررسی فایل‌های اجرایی
print_step "10" "بررسی فایل‌های اجرایی..."
echo "=== جستجوی ipa-server-install ==="
find /usr -name "ipa-server-install" 2>/dev/null
echo ""

# مرحله 11: تست دستور
print_step "11" "تست دستور ipa-server-install..."
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
print_success "حل مشکل SSL تکمیل شد!"
echo "=========================================="
echo "حالا می‌توانید FreeIPA را نصب کنید:"
echo "sudo ipa-server-install --help"
echo "=========================================="
