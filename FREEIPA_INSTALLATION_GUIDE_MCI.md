# راهنمای کامل نصب FreeIPA با یوزر MCI - سرور 192.168.0.36

## 🎯 اطلاعات سرور
- **IP Address:** 192.168.0.36
- **یوزر:** mci
- **سیستم عامل:** Red Hat 8.10
- **دامنه:** mci.local
- **نام میزبان:** ipa.mci.local
- **Realm:** MCI.LOCAL

## 🚀 مراحل نصب

### مرحله 1: ورود به سرور
```bash
ssh mci@192.168.0.36
# وارد رمز عبور یوزر mci
```

### مرحله 2: دریافت دسترسی root
```bash
sudo su -
# یا
sudo -i
# وارد رمز عبور یوزر mci
```

### مرحله 3: به‌روزرسانی سیستم
```bash
dnf update -y
dnf install -y epel-release
```

### مرحله 4: نصب FreeIPA
```bash
dnf install -y ipa-server ipa-server-dns
```

### مرحله 5: تنظیم نام میزبان
```bash
hostnamectl set-hostname ipa.mci.local
echo "192.168.0.36 ipa.mci.local ipa" >> /etc/hosts
```

### مرحله 6: نصب و پیکربندی FreeIPA
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

### مرحله 7: فعال‌سازی سرویس‌ها
```bash
systemctl enable ipa
systemctl start ipa
systemctl enable ipa-dnskeysyncd
systemctl start ipa-dnskeysyncd
```

### مرحله 8: تنظیم فایروال
```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-service=ldap
firewall-cmd --permanent --add-service=ldaps
firewall-cmd --permanent --add-service=kerberos
firewall-cmd --permanent --add-service=kpasswd
firewall-cmd --reload
```

### مرحله 9: ایجاد یوزر MCI در FreeIPA
```bash
# انتظار برای آماده شدن سرویس
sleep 10

# ایجاد یوزر MCI
ipa user-add mci \
  --first=MCI \
  --last=User \
  --email=mci@mci.local \
  --password

# دادن دسترسی ادمین به یوزر MCI
ipa group-add-member admins --users=mci

# ایجاد گروه مخصوص MCI
ipa group-add mci-admins \
  --desc="ادمین‌های MCI"

ipa group-add-member mci-admins --users=mci
```

### مرحله 10: ایجاد کاربر و گروه نمونه
```bash
# ایجاد کاربر نمونه
ipa user-add john.doe \
  --first=John \
  --last=Doe \
  --email=john.doe@mci.local \
  --password

# ایجاد گروه نمونه
ipa group-add developers \
  --desc="توسعه‌دهندگان"

# افزودن کاربر به گروه
ipa group-add-member developers --users=john.doe
```

## 🔧 تست نصب

### تست 1: بررسی وضعیت سرویس
```bash
systemctl status ipa
systemctl status ipa-dnskeysyncd
```

### تست 2: تست اتصال Kerberos
```bash
kinit admin
ipa user-find admin
kdestroy

# تست با یوزر MCI
kinit mci
ipa user-find mci
kdestroy
```

### تست 3: دسترسی به Web UI
- **آدرس:** https://192.168.0.36
- **نام کاربری:** admin یا mci
- **رمز عبور:** MySecretPassword123

## 📱 تنظیم در Flask CMS

### اطلاعات اتصال:
```
نام سرور: FreeIPA MCI Server
آدرس سرور: 192.168.0.36
پورت: 389 (یا 636 برای SSL)
SSL: ✓ (توصیه می‌شود)
Base DN: dc=mci,dc=local
Bind DN: cn=mci,cn=users,dc=mci,dc=local
رمز عبور: [رمز یوزر MCI]
```

### مراحل تنظیم در Flask CMS:
1. **ورود به Flask CMS:** http://localhost:5000
2. **ورود با:** admin / admin123
3. **رفتن به FreeIPA** در منوی کناری
4. **تنظیمات سرور** → **افزودن سرور جدید**
5. **وارد کردن اطلاعات بالا**
6. **تست اتصال**

## 🛠️ عیب‌یابی

### مشکل 1: خطای DNS
```bash
# بررسی DNS
nslookup ipa.mci.local
dig ipa.mci.local

# تنظیم DNS
ipa-dns-install --forwarder=8.8.8.8
```

### مشکل 2: خطای فایروال
```bash
# بررسی پورت‌ها
netstat -tlnp | grep -E ':(80|443|389|636|88|464)'

# باز کردن پورت‌ها
firewall-cmd --permanent --add-port=389/tcp
firewall-cmd --permanent --add-port=636/tcp
firewall-cmd --reload
```

### مشکل 3: خطای Kerberos
```bash
# بررسی تنظیمات
cat /etc/krb5.conf

# تست Kerberos
kinit mci
klist
```

## 🔐 امنیت

### تغییر رمزهای پیش‌فرض
```bash
# تغییر رمز ادمین
kinit admin
ipa user-mod admin --password

# تغییر رمز یوزر MCI
kinit mci
ipa user-mod mci --password
```

### پشتیبان‌گیری
```bash
# پشتیبان‌گیری
ipa-backup-manage backup

# بازیابی
ipa-backup-manage restore /var/lib/ipa/backup/backup-*.tar
```

## 📊 مانیتورینگ

### لاگ‌ها:
```bash
# لاگ FreeIPA
journalctl -u ipa -f

# لاگ DNS
journalctl -u ipa-dnskeysyncd -f

# لاگ سیستم
journalctl -f
```

### دستورات مفید:
```bash
# لیست کاربران
ipa user-find

# لیست گروه‌ها
ipa group-find

# اطلاعات یوزر MCI
ipa user-show mci

# اطلاعات گروه MCI
ipa group-show mci-admins
```

## 🎉 نتیجه

پس از تکمیل نصب، شما می‌توانید:

1. **از Web UI FreeIPA استفاده کنید:** https://192.168.0.36
2. **با یوزر MCI لاگین کنید**
3. **از Flask CMS برای مدیریت FreeIPA استفاده کنید**
4. **کاربران و گروه‌ها را مدیریت کنید**
5. **پیامک ارسال کنید**
6. **همگام‌سازی انجام دهید**

## 📞 پشتیبانی

اگر مشکلی داشتید، لاگ‌ها را بررسی کنید:
```bash
journalctl -u ipa -f
```

**آیا آماده شروع نصب هستید؟**



