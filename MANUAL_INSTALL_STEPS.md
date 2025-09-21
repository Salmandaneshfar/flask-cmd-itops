# راهنمای اجرای دستی اسکریپت نصب FreeIPA

## 🚀 مراحل اجرای اسکریپت ساده

### مرحله 1: کپی اسکریپت به سرور

#### روش A: استفاده از SCP (نیاز به رمز عبور)
```bash
scp install_freeipa_simple.sh mci@192.168.0.36:~/
```

#### روش B: کپی دستی محتوا
1. فایل `install_freeipa_simple.sh` را باز کنید
2. تمام محتوا را کپی کنید
3. در سرور فایل جدید ایجاد کنید:
```bash
nano install_freeipa_simple.sh
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
chmod +x install_freeipa_simple.sh

# اجرای اسکریپت
bash install_freeipa_simple.sh
```

## 📋 محتوای اسکریپت ساده (برای کپی دستی)

```bash
#!/bin/bash

# اسکریپت ساده نصب FreeIPA - سرور 192.168.0.36
# استفاده: sudo bash install_freeipa_simple.sh

echo "=== شروع نصب FreeIPA ==="
echo "IP سرور: 192.168.0.36"
echo "دامنه: mci.local"
echo "نام میزبان: ipa.mci.local"
echo

# مرحله 1: به‌روزرسانی سیستم
echo "مرحله 1: به‌روزرسانی سیستم..."
dnf update -y
dnf install -y epel-release
echo "✅ سیستم به‌روزرسانی شد"

# مرحله 2: نصب FreeIPA
echo "مرحله 2: نصب FreeIPA..."
dnf install -y ipa-server ipa-server-dns
echo "✅ FreeIPA نصب شد"

# مرحله 3: تنظیم نام میزبان
echo "مرحله 3: تنظیم نام میزبان..."
hostnamectl set-hostname ipa.mci.local
echo "192.168.0.36 ipa.mci.local ipa" >> /etc/hosts
echo "✅ نام میزبان تنظیم شد"

# مرحله 4: نصب و پیکربندی FreeIPA
echo "مرحله 4: نصب و پیکربندی FreeIPA..."
ipa-server-install \
  --domain=mci.local \
  --realm=MCI.LOCAL \
  --ds-password=MySecretPassword123 \
  --admin-password=MySecretPassword123 \
  --hostname=ipa.mci.local \
  --ip-address=192.168.0.36 \
  --setup-dns \
  --forwarder=8.8.8.8 \
  --forwarder=8.8.4.4 \
  --unattended
echo "✅ FreeIPA نصب و پیکربندی شد"

# مرحله 5: فعال‌سازی سرویس‌ها
echo "مرحله 5: فعال‌سازی سرویس‌ها..."
systemctl enable ipa
systemctl start ipa
systemctl enable ipa-dnskeysyncd
systemctl start ipa-dnskeysyncd
echo "✅ سرویس‌ها فعال شدند"

# مرحله 6: تنظیم فایروال
echo "مرحله 6: تنظیم فایروال..."
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=ldap
firewall-cmd --permanent --add-service=ldaps
firewall-cmd --permanent --add-service=kerberos
firewall-cmd --permanent --add-service=kpasswd
firewall-cmd --reload
echo "✅ فایروال تنظیم شد"

# مرحله 7: ایجاد یوزر MCI
echo "مرحله 7: ایجاد یوزر MCI..."
sleep 10

# ایجاد یوزر MCI بدون رمز عبور (بعداً تنظیم می‌شود)
ipa user-add mci \
  --first=MCI \
  --last=User \
  --email=mci@mci.local 2>/dev/null || echo "⚠️ یوزر MCI ایجاد نشد"

# دادن دسترسی ادمین به یوزر MCI
ipa group-add-member admins --users=mci 2>/dev/null || echo "⚠️ دسترسی ادمین به MCI داده نشد"

# تنظیم رمز عبور برای یوزر MCI
echo "🔐 تنظیم رمز عبور برای یوزر MCI..."
echo "لطفاً رمز عبور جدید برای یوزر MCI وارد کنید:"
ipa user-mod mci --password 2>/dev/null || echo "⚠️ رمز عبور تنظیم نشد"

echo "✅ یوزر MCI ایجاد شد"

# مرحله 8: ایجاد کاربر نمونه
echo "مرحله 8: ایجاد کاربر نمونه..."
ipa user-add john.doe \
  --first=John \
  --last=Doe \
  --email=john.doe@mci.local \
  --password 2>/dev/null || echo "⚠️ کاربر نمونه ایجاد نشد"

ipa group-add developers \
  --desc="توسعه‌دهندگان" 2>/dev/null || echo "⚠️ گروه نمونه ایجاد نشد"

ipa group-add-member developers --users=john.doe 2>/dev/null || echo "⚠️ کاربر به گروه اضافه نشد"
echo "✅ کاربر و گروه نمونه ایجاد شدند"

# نمایش اطلاعات نهایی
echo
echo "🎉 === نصب FreeIPA تکمیل شد! ==="
echo
echo "📱 اطلاعات اتصال:"
echo "Web UI: https://192.168.0.36"
echo "نام کاربری: admin یا mci"
echo "رمز عبور: MySecretPassword123"
echo "Base DN: dc=mci,dc=local"
echo
echo "📱 اطلاعات برای Flask CMS:"
echo "آدرس سرور: 192.168.0.36"
echo "پورت: 389 (یا 636 برای SSL)"
echo "Base DN: dc=mci,dc=local"
echo "Bind DN: cn=mci,cn=users,dc=mci,dc=local"
echo "رمز عبور: [رمز یوزر MCI که وارد کردید]"
echo
echo "🧪 برای تست:"
echo "kinit admin"
echo "ipa user-find admin"
echo
echo "✅ حالا می‌توانید از Flask CMS برای مدیریت FreeIPA استفاده کنید!"
```

## 🔧 مراحل پس از نصب

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

## 📱 تنظیم در Flask CMS

### اطلاعات اتصال:
```
نام سرور: FreeIPA MCI Server
آدرس سرور: 192.168.0.36
پورت: 389 (یا 636 برای SSL)
SSL: ✓ (توصیه می‌شود)
Base DN: dc=mci,dc=local
Bind DN: cn=mci,cn=users,dc=mci,dc=local
رمز عبور: [رمز یوزر MCI که وارد کردید]
```

## ✅ آماده برای شروع!

مراحل بالا را دنبال کنید و نصب را شروع کنید.



