# راهنمای نصب FreeIPA روی Red Hat 8.10

## 🎯 پیش‌نیازها

### 1️⃣ **سیستم عامل:**
- Red Hat Enterprise Linux 8.10
- حداقل 4GB RAM
- حداقل 20GB فضای خالی
- اتصال به اینترنت

### 2️⃣ **شبکه:**
- IP ثابت
- نام دامنه (مثال: ipa.example.com)
- پورت‌های باز: 80, 443, 389, 636, 88, 464

## 🚀 مراحل نصب

### مرحله 1: به‌روزرسانی سیستم
```bash
sudo dnf update -y
sudo dnf install -y epel-release
```

### مرحله 2: نصب FreeIPA Server
```bash
sudo dnf install -y ipa-server ipa-server-dns
```

### مرحله 3: تنظیم نام میزبان
```bash
# تنظیم نام میزبان
sudo hostnamectl set-hostname ipa.example.com

# اضافه کردن به /etc/hosts
echo "192.168.1.100 ipa.example.com ipa" | sudo tee -a /etc/hosts
```

### مرحله 4: نصب FreeIPA
```bash
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

### مرحله 5: فعال‌سازی سرویس‌ها
```bash
sudo systemctl enable ipa
sudo systemctl start ipa
sudo systemctl enable ipa-dnskeysyncd
sudo systemctl start ipa-dnskeysyncd
```

### مرحله 6: باز کردن پورت‌های فایروال
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ldap
sudo firewall-cmd --permanent --add-service=ldaps
sudo firewall-cmd --permanent --add-service=kerberos
sudo firewall-cmd --permanent --add-service=kpasswd
sudo firewall-cmd --reload
```

## 🔧 تنظیمات پس از نصب

### 1️⃣ **تست نصب:**
```bash
# بررسی وضعیت سرویس‌ها
sudo systemctl status ipa

# تست اتصال
kinit admin
ipa user-find admin
```

### 2️⃣ **دسترسی به Web UI:**
- آدرس: https://ipa.example.com
- نام کاربری: admin
- رمز عبور: MySecretPassword123

### 3️⃣ **تنظیم DNS:**
```bash
# اگر از DNS داخلی استفاده می‌کنید
sudo ipa-dns-install --forwarder=8.8.8.8
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

## 🛠️ عیب‌یابی

### مشکل 1: خطای DNS
```bash
# بررسی DNS
nslookup ipa.example.com
dig ipa.example.com
```

### مشکل 2: خطای فایروال
```bash
# بررسی پورت‌ها
sudo netstat -tlnp | grep -E ':(80|443|389|636|88|464)'
```

### مشکل 3: خطای Kerberos
```bash
# بررسی تنظیمات Kerberos
cat /etc/krb5.conf
```

## 🔐 امنیت

### 1️⃣ **تغییر رمزهای پیش‌فرض:**
```bash
# تغییر رمز ادمین
kinit admin
ipa user-mod admin --password
```

### 2️⃣ **تنظیم SSL:**
```bash
# بررسی گواهی SSL
ipa cert-show 1
```

### 3️⃣ **پشتیبان‌گیری:**
```bash
# پشتیبان‌گیری از FreeIPA
sudo ipa-backup-manage backup
```

## 📞 پشتیبانی

### لاگ‌ها:
```bash
# لاگ FreeIPA
sudo journalctl -u ipa -f

# لاگ DNS
sudo journalctl -u ipa-dnskeysyncd -f
```

### دستورات مفید:
```bash
# لیست کاربران
ipa user-find

# لیست گروه‌ها
ipa group-find

# ایجاد کاربر
ipa user-add john.doe --first=John --last=Doe --email=john@example.com

# ایجاد گروه
ipa group-add developers --desc="توسعه‌دهندگان"
```

---

**🎉 پس از نصب، می‌توانید از Flask CMS برای مدیریت FreeIPA استفاده کنید!**

