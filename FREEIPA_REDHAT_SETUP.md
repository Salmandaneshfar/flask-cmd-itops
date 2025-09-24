# راهنمای کامل نصب FreeIPA روی Red Hat 8.10

## 🎯 مراحل نصب

### 1️⃣ **آماده‌سازی سرور Red Hat 8.10**

```bash
# ورود به سرور Red Hat
ssh root@your-server-ip

# به‌روزرسانی سیستم
sudo dnf update -y
sudo dnf install -y epel-release
```

### 2️⃣ **نصب FreeIPA Server**

```bash
# نصب بسته‌های مورد نیاز
sudo dnf install -y ipa-server ipa-server-dns

# تنظیم نام میزبان
sudo hostnamectl set-hostname ipa.example.com

# اضافه کردن به /etc/hosts
echo "192.168.1.100 ipa.example.com ipa" | sudo tee -a /etc/hosts
```

### 3️⃣ **نصب و پیکربندی FreeIPA**

```bash
# اجرای نصب
sudo ipa-server-install \
  --domain=example.com \
  --realm=EXAMPLE.COM \
  --ds-password=MySecretPassword123 \
  --admin-password=MySecretPassword123 \
  --hostname=ipa.example.com \
  --ip-address=192.168.1.100 \
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

- **آدرس:** https://ipa.example.com
- **نام کاربری:** admin
- **رمز عبور:** MySecretPassword123

### 3️⃣ **ایجاد کاربر و گروه نمونه**

```bash
# ایجاد کاربر نمونه
ipa user-add john.doe \
  --first=John \
  --last=Doe \
  --email=john.doe@example.com \
  --password

# ایجاد گروه نمونه
ipa group-add developers \
  --desc="توسعه‌دهندگان"

# افزودن کاربر به گروه
ipa group-add-member developers --users=john.doe
```

## 📱 تنظیم در Flask CMS

### اطلاعات اتصال:

```
نام سرور: FreeIPA Server
آدرس سرور: ipa.example.com (یا IP سرور)
پورت: 389 (یا 636 برای SSL)
SSL: ✓ (توصیه می‌شود)
Base DN: dc=example,dc=com
Bind DN: cn=admin,cn=users,dc=example,dc=com
رمز عبور: MySecretPassword123
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
nslookup ipa.example.com
dig ipa.example.com

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

# تست Kerberos
kinit admin
klist
```

## 🔐 امنیت

### 1️⃣ **تغییر رمزهای پیش‌فرض**
```bash
# تغییر رمز ادمین
kinit admin
ipa user-mod admin --password
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

# اطلاعات کاربر
ipa user-show john.doe

# اطلاعات گروه
ipa group-show developers
```

## 🎉 نتیجه

پس از تکمیل نصب، شما می‌توانید:

1. **از Web UI FreeIPA استفاده کنید**
2. **از Flask CMS برای مدیریت FreeIPA استفاده کنید**
3. **کاربران و گروه‌ها را مدیریت کنید**
4. **پیامک ارسال کنید**
5. **همگام‌سازی انجام دهید**

**آیا سوال خاصی در مورد نصب دارید؟**








