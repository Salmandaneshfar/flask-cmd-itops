# راهنمای نصب FreeIPA با یوزر MCI - IP: 192.168.0.36

## 🎯 تنظیمات مخصوص سرور شما

### اطلاعات سرور:
- **IP Address:** 192.168.0.36
- **نام دامنه:** mci.local
- **نام میزبان:** ipa.mci.local
- **Realm:** MCI.LOCAL
- **یوزر ادمین:** mci

## 🚀 مراحل نصب

### 1️⃣ **آماده‌سازی سرور Red Hat 8.10**

```bash
# ورود به سرور
ssh root@192.168.0.36

# به‌روزرسانی سیستم
sudo dnf update -y
sudo dnf install -y epel-release
```

### 2️⃣ **نصب FreeIPA Server**

```bash
# نصب بسته‌های مورد نیاز
sudo dnf install -y ipa-server ipa-server-dns

# تنظیم نام میزبان
sudo hostnamectl set-hostname ipa.mci.local

# اضافه کردن به /etc/hosts
echo "192.168.0.36 ipa.mci.local ipa" | sudo tee -a /etc/hosts
```

### 3️⃣ **نصب و پیکربندی FreeIPA**

```bash
# اجرای نصب
sudo ipa-server-install \
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

### 4️⃣ **فعال‌سازی سرویس‌ها**

```bash
# فعال‌سازی سرویس‌ها
sudo systemctl enable ipa
sudo systemctl start ipa
sudo systemctl enable ipa-dnskeysyncd
sudo systemctl start ipa-dnskeysyncd

# بررسی وضعیت
sudo systemctl status ipa
```

### 5️⃣ **تنظیم فایروال**

```bash
# باز کردن پورت‌های مورد نیاز
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ldap
sudo firewall-cmd --permanent --add-service=ldaps
sudo firewall-cmd --permanent --add-service=kerberos
sudo firewall-cmd --permanent --add-service=kpasswd
sudo firewall-cmd --reload

# بررسی پورت‌های باز
sudo firewall-cmd --list-all
```

## 🔧 تنظیمات پس از نصب

### 1️⃣ **تست نصب**

```bash
# تست اتصال
kinit admin
ipa user-find admin

# خروج از Kerberos
kdestroy
```

### 2️⃣ **دسترسی به Web UI**

- **آدرس:** https://192.168.0.36
- **نام کاربری:** admin
- **رمز عبور:** MySecretPassword123

### 3️⃣ **ایجاد یوزر MCI**

```bash
# ایجاد یوزر MCI
ipa user-add mci \
  --first=MCI \
  --last=User \
  --email=mci@mci.local \
  --password

# دادن دسترسی ادمین به یوزر MCI
ipa group-add-member admins --users=mci

# یا ایجاد گروه مخصوص MCI
ipa group-add mci-admins \
  --desc="ادمین‌های MCI"

ipa group-add-member mci-admins --users=mci
```

### 4️⃣ **ایجاد کاربر و گروه نمونه**

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

## 📱 تنظیم در Flask CMS

### اطلاعات اتصال برای Flask CMS:

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
sudo ipa-dns-install --forwarder=8.8.8.8
```

### مشکل 2: خطای فایروال
```bash
# بررسی پورت‌ها
sudo netstat -tlnp | grep -E ':(80|443|389|636|88|464)'

# باز کردن پورت‌ها
sudo firewall-cmd --permanent --add-port=389/tcp
sudo firewall-cmd --permanent --add-port=636/tcp
sudo firewall-cmd --reload
```

### مشکل 3: خطای Kerberos
```bash
# بررسی تنظیمات
cat /etc/krb5.conf

# تست Kerberos با یوزر MCI
kinit mci
klist
```

## 🔐 امنیت

### 1️⃣ **تغییر رمزهای پیش‌فرض**
```bash
# تغییر رمز ادمین
kinit admin
ipa user-mod admin --password

# تغییر رمز یوزر MCI
kinit mci
ipa user-mod mci --password
```

### 2️⃣ **پشتیبان‌گیری**
```bash
# پشتیبان‌گیری
sudo ipa-backup-manage backup

# بازیابی
sudo ipa-backup-manage restore /var/lib/ipa/backup/backup-*.tar
```

## 📊 مانیتورینگ

### لاگ‌ها:
```bash
# لاگ FreeIPA
sudo journalctl -u ipa -f

# لاگ DNS
sudo journalctl -u ipa-dnskeysyncd -f

# لاگ سیستم
sudo journalctl -f
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
sudo journalctl -u ipa -f
```

**آیا سوال خاصی در مورد نصب با یوزر MCI دارید؟**






