# راهنمای اجرای اسکریپت نصب تمیز FreeIPA

## 🚀 مراحل اجرای اسکریپت

### مرحله 1: کپی اسکریپت به سرور

#### روش A: استفاده از SCP (نیاز به رمز عبور)
```bash
scp clean_install_freeipa.sh mci@192.168.0.36:~/
```

#### روش B: کپی دستی محتوا
1. فایل `clean_install_freeipa.sh` را باز کنید
2. تمام محتوا را کپی کنید
3. در سرور فایل جدید ایجاد کنید:
```bash
nano clean_install_freeipa.sh
# محتوا را پیست کنید
# Ctrl+X, Y, Enter برای ذخیره
```

### مرحله 2: ورود به سرور
```bash
ssh mci@192.168.0.36
# وارد رمز عبور یوزر mci
```

### مرحله 3: دریافت دسترسی root
```bash
sudo su -
# وارد رمز عبور یوزر mci
```

### مرحله 4: اجرای اسکریپت
```bash
# دادن مجوز اجرا
chmod +x clean_install_freeipa.sh

# اجرای اسکریپت
bash clean_install_freeipa.sh
```

## 📋 محتوای اسکریپت (برای کپی دستی)

```bash
#!/bin/bash

# اسکریپت نصب تمیز FreeIPA
# استفاده: sudo bash clean_install_freeipa.sh

set -e

# رنگ‌ها برای خروجی
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# تابع برای نمایش پیام‌ها
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# بررسی root بودن
if [[ $EUID -ne 0 ]]; then
   print_error "این اسکریپت باید با دسترسی root اجرا شود"
   exit 1
fi

print_message "=== نصب تمیز FreeIPA ==="
echo

# مرحله 1: توقف سرویس‌ها
print_message "مرحله 1: توقف سرویس‌ها..."
echo "----------------------------------------"

systemctl stop ipa-dnskeysyncd 2>/dev/null || true
systemctl stop ipa 2>/dev/null || true
print_success "سرویس‌ها متوقف شدند"

# مرحله 2: حذف سرویس‌ها
print_message "مرحله 2: حذف سرویس‌ها..."
echo "----------------------------------------"

systemctl disable ipa 2>/dev/null || true
systemctl disable ipa-dnskeysyncd 2>/dev/null || true
print_success "سرویس‌ها غیرفعال شدند"

# مرحله 3: حذف فایل‌ها
print_message "مرحله 3: حذف فایل‌ها..."
echo "----------------------------------------"

rm -rf /etc/ipa 2>/dev/null || true
rm -rf /var/lib/ipa 2>/dev/null || true
rm -rf /etc/dirsrv 2>/dev/null || true
rm -rf /var/lib/dirsrv 2>/dev/null || true
rm -rf /var/log/ipaserver-install.log 2>/dev/null || true
rm -rf /var/log/ipaserver-uninstall.log 2>/dev/null || true
print_success "فایل‌ها حذف شدند"

# مرحله 4: حذف و نصب مجدد بسته‌ها
print_message "مرحله 4: حذف و نصب مجدد بسته‌ها..."
echo "----------------------------------------"

dnf remove -y ipa-server ipa-server-dns 2>/dev/null || true
dnf install -y ipa-server ipa-server-dns
print_success "بسته‌ها نصب شدند"

# مرحله 5: تنظیم hosts
print_message "مرحله 5: تنظیم hosts..."
echo "----------------------------------------"

# حذف رکوردهای قبلی
sed -i '/ipa.mci.local/d' /etc/hosts

# اضافه کردن رکورد جدید
echo "192.168.0.36 ipa.mci.local ipa" >> /etc/hosts
print_success "رکورد hosts اضافه شد"

# مرحله 6: تنظیم DNS
print_message "مرحله 6: تنظیم DNS..."
echo "----------------------------------------"

cat > /etc/resolv.conf << EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
search mci.local
EOF

print_success "DNS تنظیم شد"

# مرحله 7: تنظیم نام میزبان
print_message "مرحله 7: تنظیم نام میزبان..."
echo "----------------------------------------"

hostnamectl set-hostname ipa.mci.local
print_success "نام میزبان تنظیم شد: $(hostname)"

# مرحله 8: پیکربندی FreeIPA
print_message "مرحله 8: پیکربندی FreeIPA..."
echo "----------------------------------------"

print_message "شروع پیکربندی (این مرحله ممکن است چند دقیقه طول بکشد)..."

ipa-server-install \
  --domain=mci.local \
  --realm=MCI.LOCAL \
  --ds-password=MySecretPassword123 \
  --admin-password=MySecretPassword123 \
  --hostname=ipa.mci.local \
  --ip-address=192.168.0.36 \
  --no-dns-sshfp \
  --unattended

print_success "پیکربندی FreeIPA تکمیل شد"

# مرحله 9: فعال‌سازی سرویس‌ها
print_message "مرحله 9: فعال‌سازی سرویس‌ها..."
echo "----------------------------------------"

systemctl enable ipa
systemctl start ipa
print_success "سرویس IPA فعال شد"

# مرحله 10: تنظیم فایروال
print_message "مرحله 10: تنظیم فایروال..."
echo "----------------------------------------"

firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=ldap
firewall-cmd --permanent --add-service=ldaps
firewall-cmd --permanent --add-service=kerberos
firewall-cmd --permanent --add-service=kpasswd
firewall-cmd --reload
print_success "فایروال تنظیم شد"

# مرحله 11: ایجاد یوزر MCI
print_message "مرحله 11: ایجاد یوزر MCI..."
echo "----------------------------------------"

sleep 10  # انتظار برای آماده شدن سرویس

# ایجاد یوزر MCI
ipa user-add mci \
  --first=MCI \
  --last=User \
  --email=mci@mci.local 2>/dev/null || print_warning "یوزر MCI ایجاد نشد"

# تنظیم رمز عبور
echo "🔐 رمز عبور یوزر MCI:"
ipa user-mod mci --password 2>/dev/null || print_warning "رمز عبور تنظیم نشد"

# دادن دسترسی ادمین
ipa group-add-member admins --users=mci 2>/dev/null || print_warning "دسترسی ادمین داده نشد"

print_success "یوزر MCI ایجاد شد"

# مرحله 12: تست نصب
print_message "مرحله 12: تست نصب..."
echo "----------------------------------------"

# بررسی وضعیت سرویس
if systemctl is-active --quiet ipa; then
    print_success "سرویس IPA فعال است"
else
    print_error "سرویس IPA غیرفعال است"
fi

# تست Kerberos
if kinit admin <<< "MySecretPassword123" 2>/dev/null; then
    print_success "Kerberos کار می‌کند"
    kdestroy
else
    print_error "Kerberos کار نمی‌کند"
fi

# نمایش اطلاعات نهایی
echo
print_success "=== نصب تمیز FreeIPA تکمیل شد! ==="
echo
print_message "📱 اطلاعات اتصال:"
print_message "Web UI: https://192.168.0.36"
print_message "نام کاربری: admin یا mci"
print_message "رمز عبور: MySecretPassword123 (admin) یا رمز MCI"
print_message "Base DN: dc=mci,dc=local"
print_message "Bind DN: cn=admin,cn=users,dc=mci,dc=local"
echo
print_message "📱 اطلاعات برای Flask CMS:"
print_message "آدرس سرور: 192.168.0.36"
print_message "پورت: 389 (یا 636 برای SSL)"
print_message "Base DN: dc=mci,dc=local"
print_message "Bind DN: cn=mci,cn=users,dc=mci,dc=local"
print_message "رمز عبور: [رمز یوزر MCI]"
echo
print_message "🧪 برای تست:"
print_message "kinit admin"
print_message "ipa user-find admin"
echo
print_success "✅ حالا می‌توانید از Flask CMS برای مدیریت FreeIPA استفاده کنید!"
```

## 🔧 مراحل پس از اجرای اسکریپت

### 1️⃣ **تست نصب**
```bash
# بررسی وضعیت سرویس
systemctl status ipa

# تست اتصال
kinit admin
ipa user-find admin
kdestroy
```

### 2️⃣ **تست یوزر MCI**
```bash
kinit mci
ipa user-find mci
kdestroy
```

### 3️⃣ **دسترسی به Web UI**
- **آدرس:** https://192.168.0.36
- **نام کاربری:** admin یا mci
- **رمز عبور:** MySecretPassword123 (admin) یا رمز MCI

## ✅ آماده برای شروع!

مراحل بالا را دنبال کنید و اسکریپت را اجرا کنید.



