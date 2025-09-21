# راهنمای نصب FreeIPA روی Windows

## 🎯 گزینه‌های نصب

### 1️⃣ **Docker (توصیه می‌شود)**
- **مزایا:** ساده، سریع، قابل حمل
- **معایب:** نیاز به Docker Desktop
- **زمان نصب:** 10-15 دقیقه

### 2️⃣ **WSL2 (Windows Subsystem for Linux)**
- **مزایا:** یکپارچه با Windows، عملکرد خوب
- **معایب:** نیاز به WSL2
- **زمان نصب:** 20-30 دقیقه

### 3️⃣ **VirtualBox با Linux**
- **مزایا:** کامل، مستقل
- **معایب:** نیاز به منابع بیشتر
- **زمان نصب:** 30-45 دقیقه

## 🚀 روش 1: Docker

### پیش‌نیازها:
- Docker Desktop نصب شده
- حداقل 4GB RAM
- حداقل 10GB فضای خالی

### مراحل نصب:

#### 1️⃣ **نصب Docker Desktop**
```bash
# دانلود از: https://www.docker.com/products/docker-desktop
# نصب و راه‌اندازی
```

#### 2️⃣ **اجرای FreeIPA**
```bash
# اجرای Docker Compose
docker-compose -f docker-freeipa-setup.yml up -d

# بررسی وضعیت
docker ps
docker logs freeipa-server
```

#### 3️⃣ **دسترسی به FreeIPA**
- **Web UI:** https://localhost
- **یوزر:** admin
- **رمز:** MySecretPassword123

## 🚀 روش 2: WSL2

### پیش‌نیازها:
- Windows 10/11 با WSL2
- Ubuntu 20.04+ در WSL2

### مراحل نصب:

#### 1️⃣ **نصب WSL2**
```powershell
# در PowerShell به عنوان Administrator
wsl --install
wsl --set-default-version 2
```

#### 2️⃣ **نصب Ubuntu**
```bash
# از Microsoft Store نصب کنید
# یا از command line:
wsl --install -d Ubuntu
```

#### 3️⃣ **اجرای اسکریپت نصب**
```bash
# ورود به WSL2
wsl

# دریافت دسترسی root
sudo su -

# اجرای اسکریپت
bash install-freeipa-wsl.sh
```

## 🚀 روش 3: VirtualBox

### پیش‌نیازها:
- VirtualBox نصب شده
- حداقل 4GB RAM
- حداقل 20GB فضای خالی

### مراحل نصب:

#### 1️⃣ **نصب VirtualBox**
```bash
# دانلود از: https://www.virtualbox.org/
# نصب و راه‌اندازی
```

#### 2️⃣ **ایجاد VM**
- **OS:** Ubuntu Server 20.04+
- **RAM:** 4GB
- **Storage:** 20GB
- **Network:** Bridge Adapter

#### 3️⃣ **نصب FreeIPA در VM**
```bash
# ورود به VM
ssh user@vm-ip

# دریافت دسترسی root
sudo su -

# اجرای اسکریپت نصب
bash install-freeipa-wsl.sh
```

## 📱 تنظیم Flask CMS

### اطلاعات اتصال:

#### برای Docker:
```
نام سرور: FreeIPA Docker
آدرس سرور: localhost
پورت: 389
SSL: خیر
Base DN: dc=local
Bind DN: cn=admin,cn=users,dc=local
رمز عبور: MySecretPassword123
```

#### برای WSL2:
```
نام سرور: FreeIPA WSL2
آدرس سرور: localhost
پورت: 389
SSL: خیر
Base DN: dc=local
Bind DN: cn=mci,cn=users,dc=local
رمز عبور: [رمز یوزر MCI]
```

#### برای VirtualBox:
```
نام سرور: FreeIPA VM
آدرس سرور: [IP VM]
پورت: 389
SSL: خیر
Base DN: dc=local
Bind DN: cn=mci,cn=users,dc=local
رمز عبور: [رمز یوزر MCI]
```

## 🔧 عیب‌یابی

### مشکل 1: Docker
```bash
# بررسی وضعیت
docker ps
docker logs freeipa-server

# راه‌اندازی مجدد
docker-compose -f docker-freeipa-setup.yml restart
```

### مشکل 2: WSL2
```bash
# بررسی وضعیت
systemctl status ipa

# راه‌اندازی مجدد
sudo systemctl restart ipa
```

### مشکل 3: VirtualBox
```bash
# بررسی شبکه
ip addr show

# بررسی فایروال
sudo ufw status
```

## ✅ تست نصب

### تست 1: Web UI
- **آدرس:** https://localhost (Docker/WSL2) یا https://vm-ip (VirtualBox)
- **یوزر:** admin
- **رمز:** MySecretPassword123

### تست 2: Flask CMS
1. **ورود به Flask CMS:** http://localhost:5000
2. **منو:** FreeIPA → تنظیمات سرور
3. **افزودن سرور جدید** با اطلاعات بالا
4. **تست اتصال**

## 🎉 نتیجه

پس از تکمیل نصب:
- ✅ FreeIPA نصب و پیکربندی شده
- ✅ Web UI در دسترس است
- ✅ آماده برای اتصال به Flask CMS
- ✅ مدیریت کاربران و گروه‌ها فعال است

## ❓ سوال

کدام روش را ترجیح می‌دهید؟
- **A)** Docker (ساده‌ترین)
- **B)** WSL2 (یکپارچه با Windows)
- **C)** VirtualBox (کامل و مستقل)

کدام گزینه را انتخاب می‌کنید؟



