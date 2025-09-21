# راهنمای نصب امن FreeIPA - سرور 192.168.0.36

## 🔐 نصب امن با رمزهای عبور پویا

### گزینه 1: اسکریپت امن (توصیه می‌شود)
```bash
# کپی اسکریپت به سرور
scp install_freeipa_secure.sh mci@192.168.0.36:~/

# ورود به سرور
ssh mci@192.168.0.36

# دریافت دسترسی root
sudo su -

# اجرای اسکریپت امن
bash install_freeipa_secure.sh
```

### گزینه 2: نصب دستی با رمزهای عبور امن

#### 1️⃣ **ورود به سرور**
```bash
ssh mci@192.168.0.36
sudo su -
```

#### 2️⃣ **به‌روزرسانی سیستم**
```bash
dnf update -y
dnf install -y epel-release
```

#### 3️⃣ **نصب FreeIPA**
```bash
dnf install -y ipa-server ipa-server-dns
```

#### 4️⃣ **تنظیم نام میزبان**
```bash
hostnamectl set-hostname ipa.mci.local
echo "192.168.0.36 ipa.mci.local ipa" >> /etc/hosts
```

#### 5️⃣ **نصب و پیکربندی FreeIPA**
```bash
# رمزهای عبور را از کاربر دریافت کنید
echo "رمز عبور ادمین FreeIPA:"
read -s ADMIN_PASS
echo "رمز عبور Directory Server:"
read -s DS_PASS

ipa-server-install \
  --domain=mci.local \
  --realm=MCI.LOCAL \
  --ds-password="$DS_PASS" \
  --admin-password="$ADMIN_PASS" \
  --hostname=ipa.mci.local \
  --ip-address=192.168.0.36 \
  --setup-dns \
  --forwarder=8.8.8.8 \
  --forwarder=8.8.4.4 \
  --unattended
```

#### 6️⃣ **فعال‌سازی سرویس‌ها**
```bash
systemctl enable ipa
systemctl start ipa
systemctl enable ipa-dnskeysyncd
systemctl start ipa-dnskeysyncd
```

#### 7️⃣ **تنظیم فایروال**
```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=ldap
firewall-cmd --permanent --add-service=ldaps
firewall-cmd --permanent --add-service=kerberos
firewall-cmd --permanent --add-service=kpasswd
firewall-cmd --reload
```

#### 8️⃣ **ایجاد یوزر MCI**
```bash
sleep 10

# ایجاد یوزر MCI
ipa user-add mci \
  --first=MCI \
  --last=User \
  --email=mci@mci.local

# تنظیم رمز عبور
echo "رمز عبور یوزر MCI:"
read -s MCI_PASS
echo "$MCI_PASS" | ipa user-mod mci --password

# دادن دسترسی ادمین
ipa group-add-member admins --users=mci
```

#### 9️⃣ **ایجاد کاربر نمونه**
```bash
# ایجاد کاربر نمونه
ipa user-add john.doe \
  --first=John \
  --last=Doe \
  --email=john.doe@mci.local

# تنظیم رمز عبور
echo "Password123" | ipa user-mod john.doe --password

# ایجاد گروه
ipa group-add developers --desc="توسعه‌دهندگان"
ipa group-add-member developers --users=john.doe
```

## 🛡️ نکات امنیتی

### ✅ **کارهای درست:**
- استفاده از رمزهای عبور قوی
- تغییر رمزهای پیش‌فرض
- استفاده از SSL/TLS
- پشتیبان‌گیری منظم
- مانیتورینگ لاگ‌ها

### ❌ **کارهای نادرست:**
- استفاده از رمزهای عبور ضعیف
- hardcode کردن رمزها در اسکریپت‌ها
- عدم تغییر رمزهای پیش‌فرض
- عدم استفاده از SSL

## 🔧 تست نصب

### تست 1: بررسی وضعیت
```bash
systemctl status ipa
systemctl status ipa-dnskeysyncd
```

### تست 2: تست اتصال
```bash
kinit admin
ipa user-find admin
kdestroy
```

### تست 3: تست یوزر MCI
```bash
kinit mci
ipa user-find mci
kdestroy
```

## 📱 تنظیم در Flask CMS

### اطلاعات اتصال:
```
نام سرور: FreeIPA MCI Server
آدرس سرور: 192.168.0.36
پورت: 636 (SSL)
SSL: ✓
Base DN: dc=mci,dc=local
Bind DN: cn=mci,cn=users,dc=mci,dc=local
رمز عبور: [رمز یوزر MCI که وارد کردید]
```

## 🎯 نتیجه

پس از تکمیل نصب امن:

1. **FreeIPA با رمزهای عبور امن نصب شده**
2. **یوزر MCI با دسترسی ادمین ایجاد شده**
3. **فایروال تنظیم شده**
4. **SSL فعال است**
5. **آماده برای اتصال به Flask CMS**

## 📞 پشتیبانی

اگر مشکلی داشتید:
```bash
journalctl -u ipa -f
```

**آیا آماده شروع نصب امن هستید؟**



