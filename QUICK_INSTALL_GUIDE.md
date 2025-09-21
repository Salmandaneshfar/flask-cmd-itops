# راهنمای سریع نصب FreeIPA - سرور 192.168.0.36

## 🚀 مراحل سریع نصب

### 1️⃣ **ورود به سرور**
```bash
ssh mci@192.168.0.36
# وارد رمز عبور یوزر mci
```

### 2️⃣ **دریافت دسترسی root**
```bash
sudo su -
# وارد رمز عبور یوزر mci
```

### 3️⃣ **اجرای مراحل نصب (کپی و پیست کنید)**

#### مرحله 1: به‌روزرسانی سیستم
```bash
dnf update -y
dnf install -y epel-release
```

#### مرحله 2: نصب FreeIPA
```bash
dnf install -y ipa-server ipa-server-dns
```

#### مرحله 3: تنظیم نام میزبان
```bash
hostnamectl set-hostname ipa.mci.local
echo "192.168.0.36 ipa.mci.local ipa" >> /etc/hosts
```

#### مرحله 4: نصب و پیکربندی FreeIPA
```bash
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
```

#### مرحله 5: فعال‌سازی سرویس‌ها
```bash
systemctl enable ipa
systemctl start ipa
systemctl enable ipa-dnskeysyncd
systemctl start ipa-dnskeysyncd
```

#### مرحله 6: تنظیم فایروال
```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=ldap
firewall-cmd --permanent --add-service=ldaps
firewall-cmd --permanent --add-service=kerberos
firewall-cmd --permanent --add-service=kpasswd
firewall-cmd --reload
```

#### مرحله 7: ایجاد یوزر MCI
```bash
sleep 10
ipa user-add mci \
  --first=MCI \
  --last=User \
  --email=mci@mci.local \
  --password

ipa group-add-member admins --users=mci
ipa group-add mci-admins --desc="ادمین‌های MCI"
ipa group-add-member mci-admins --users=mci
```

#### مرحله 8: ایجاد کاربر نمونه
```bash
ipa user-add john.doe \
  --first=John \
  --last=Doe \
  --email=john.doe@mci.local \
  --password

ipa group-add developers --desc="توسعه‌دهندگان"
ipa group-add-member developers --users=john.doe
```

### 4️⃣ **تست نصب**
```bash
systemctl status ipa
kinit admin
ipa user-find admin
kdestroy
```

## 🎯 اطلاعات مهم

- **Web UI:** https://192.168.0.36
- **نام کاربری:** admin یا mci
- **رمز عبور:** MySecretPassword123
- **دامنه:** mci.local
- **Base DN:** dc=mci,dc=local

## 📱 تنظیم در Flask CMS

```
نام سرور: FreeIPA MCI Server
آدرس سرور: 192.168.0.36
پورت: 389 (یا 636 برای SSL)
SSL: ✓
Base DN: dc=mci,dc=local
Bind DN: cn=mci,cn=users,dc=mci,dc=local
رمز عبور: [رمز یوزر MCI]
```

## ✅ آماده برای شروع!

تمام مراحل بالا را کپی کنید و در ترمینال سرور اجرا کنید.



