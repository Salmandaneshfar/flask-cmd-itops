#!/bin/bash

echo "=== حل مشکل Python Certificate و نصب FreeIPA ==="

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
echo "Python Version: $(python3 --version)"
echo ""

# مرحله 2: حل مشکل Python Certificate
print_step "2" "حل مشکل Python Certificate..."
# نصب certificate های جدید
dnf install -y ca-certificates python3-requests python3-urllib3
# به‌روزرسانی certificate bundle
update-ca-trust
print_success "Certificate ها به‌روزرسانی شدند"

# مرحله 3: بررسی فایل‌های certificate
print_step "3" "بررسی فایل‌های certificate..."
echo "=== بررسی فایل‌های certificate ==="
ls -la /etc/pki/tls/certs/ca-bundle.crt
ls -la /etc/pki/tls/certs/ca-bundle.trust.crt
echo ""

# مرحله 4: توقف سرویس‌ها
print_step "4" "توقف سرویس‌ها..."
systemctl stop ipa 2>/dev/null || true
systemctl stop ipa-dnskeysyncd 2>/dev/null || true
systemctl stop dirsrv@MCI-LOCAL 2>/dev/null || true
systemctl stop krb5kdc 2>/dev/null || true
systemctl stop kadmin 2>/dev/null || true
print_success "سرویس‌ها متوقف شدند"

# مرحله 5: حذف تنظیمات ناقص
print_step "5" "حذف تنظیمات ناقص..."
rm -rf /etc/ipa 2>/dev/null || true
rm -rf /var/lib/ipa 2>/dev/null || true
rm -rf /etc/dirsrv 2>/dev/null || true
rm -rf /var/lib/dirsrv 2>/dev/null || true
rm -rf /etc/krb5.conf 2>/dev/null || true
rm -rf /var/kerberos 2>/dev/null || true
print_success "تنظیمات ناقص حذف شدند"

# مرحله 6: تنظیم hostname و hosts
print_step "6" "تنظیم hostname و hosts..."
hostnamectl set-hostname ipa.mci.local
sed -i '/ipa.mci.local/d' /etc/hosts
echo "192.168.0.36 ipa.mci.local ipa" >> /etc/hosts
print_success "Hostname و hosts تنظیم شدند"

# مرحله 7: تنظیم DNS
print_step "7" "تنظیم DNS..."
cat > /etc/resolv.conf << EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 192.168.0.36
search mci.local
EOF
print_success "DNS تنظیم شد"

# مرحله 8: تنظیم firewall
print_step "8" "تنظیم firewall..."
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=ldap
firewall-cmd --permanent --add-service=ldaps
firewall-cmd --permanent --add-service=kerberos
firewall-cmd --permanent --add-service=kpasswd
firewall-cmd --permanent --add-service=dns
firewall-cmd --reload
print_success "Firewall تنظیم شد"

# مرحله 9: نصب FreeIPA
print_step "9" "نصب FreeIPA..."
ipa-server-install \
  --domain=mci.local \
  --realm=MCI.LOCAL \
  --ds-password=MySecretPassword123 \
  --admin-password=MySecretPassword123 \
  --hostname=ipa.mci.local \
  --ip-address=192.168.0.36 \
  --no-dns-sshfp \
  --unattended

if [ $? -eq 0 ]; then
    print_success "FreeIPA نصب شد"
else
    print_error "خطا در نصب FreeIPA"
    echo "بررسی لاگ:"
    tail -20 /var/log/ipaserver-install.log
    exit 1
fi

# مرحله 10: راه‌اندازی سرویس‌ها
print_step "10" "راه‌اندازی سرویس‌ها..."
systemctl enable ipa
systemctl start ipa
systemctl enable ipa-dnskeysyncd
systemctl start ipa-dnskeysyncd
print_success "سرویس‌ها راه‌اندازی شدند"

# مرحله 11: صبر برای آماده شدن
print_step "11" "صبر برای آماده شدن سرویس‌ها..."
sleep 60

# مرحله 12: بررسی وضعیت
print_step "12" "بررسی وضعیت سرویس‌ها..."
systemctl status ipa --no-pager -l
echo ""

# مرحله 13: ایجاد کاربر MCI
print_step "13" "ایجاد کاربر MCI..."
ipa user-add mci \
  --first=MCI \
  --last=User \
  --email=mci@mci.local \
  --password

if [ $? -eq 0 ]; then
    print_success "کاربر MCI ایجاد شد"
else
    print_warning "کاربر MCI ایجاد نشد (ممکن است قبلاً وجود داشته باشد)"
fi

# مرحله 14: دادن دسترسی ادمین به MCI
print_step "14" "دادن دسترسی ادمین به MCI..."
ipa group-add-member admins --users=mci
print_success "دسترسی ادمین به MCI داده شد"

# مرحله 15: تست اتصال
print_step "15" "تست اتصال..."
echo "=== تست اتصال LDAP محلی ==="
ldapsearch -x -H ldap://localhost -b 'dc=mci,dc=local' -D 'cn=admin,cn=users,dc=mci,dc=local' -w MySecretPassword123 2>&1 | head -5
echo ""

# مرحله 16: بررسی پورت‌ها
print_step "16" "بررسی پورت‌ها..."
echo "=== پورت‌های در حال گوش دادن ==="
netstat -tlnp | grep -E ':(389|636|80|443|88|464)'
echo ""

# مرحله 17: نمایش اطلاعات نهایی
echo ""
echo "=========================================="
if systemctl is-active --quiet ipa; then
    print_success "FreeIPA با موفقیت نصب و پیکربندی شد!"
    echo "=========================================="
    echo "🌐 Web UI: https://192.168.0.36"
    echo "👤 Admin User: admin"
    echo "🔐 Admin Password: MySecretPassword123"
    echo "👤 MCI User: mci"
    echo "🔐 MCI Password: (همان رمز وارد شده)"
    echo "=========================================="
    echo ""
    echo "برای تست اتصال:"
    echo "ldapsearch -x -H ldap://192.168.0.36 -b 'dc=mci,dc=local' -D 'cn=admin,cn=users,dc=mci,dc=local' -w MySecretPassword123"
    echo ""
else
    print_error "FreeIPA نصب نشده است!"
    echo "=========================================="
    echo "لطفاً لاگ‌ها را بررسی کنید:"
    echo "journalctl -u ipa --no-pager -l -n 50"
    echo "tail -50 /var/log/ipaserver-install.log"
    echo "=========================================="
fi
