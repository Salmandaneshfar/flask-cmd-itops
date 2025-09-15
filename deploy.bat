@echo off
REM اسکریپت deployment برای Windows
REM استفاده: deploy.bat [environment]

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production

set PROJECT_NAME=flask-cms
set DOCKER_COMPOSE_FILE=docker-compose.yml
set BACKUP_DIR=backups
set LOG_DIR=logs

echo 🚀 شروع deployment برای محیط %ENVIRONMENT%

REM بررسی وجود Docker و Docker Compose
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker نصب نیست. لطفاً ابتدا Docker را نصب کنید.
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose نصب نیست. لطفاً ابتدا Docker Compose را نصب کنید.
    exit /b 1
)

REM ایجاد دایرکتوری‌های مورد نیاز
echo 📁 ایجاد دایرکتوری‌های مورد نیاز...
if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%
if not exist %LOG_DIR% mkdir %LOG_DIR%
if not exist static\uploads mkdir static\uploads
if not exist ssl mkdir ssl

REM کپی فایل .env اگر وجود ندارد
if not exist .env (
    echo 📋 کپی فایل env.example به .env...
    copy env.example .env
    echo ⚠️ لطفاً فایل .env را ویرایش کنید و تنظیمات مناسب را وارد کنید.
    echo 🔑 خصوصاً SECRET_KEY را تغییر دهید!
    set /p "reply=آیا فایل .env را ویرایش کرده‌اید؟ (y/n): "
    if not "!reply!"=="y" (
        echo ❌ لطفاً ابتدا فایل .env را ویرایش کنید.
        exit /b 1
    )
)

REM ایجاد SSL certificate خودامضا (برای تست)
if not exist ssl\cert.pem (
    echo 🔐 ایجاد SSL certificate خودامضا...
    REM در Windows نیاز به OpenSSL یا استفاده از PowerShell
    echo ایجاد certificate با PowerShell...
    powershell -Command "& {New-SelfSignedCertificate -DnsName 'localhost' -CertStoreLocation 'Cert:\LocalMachine\My' -KeyUsage DigitalSignature,KeyEncipherment -TextExtension @('2.5.29.37={text}1.3.6.1.5.5.7.3.1')}"
)

REM بکاپ از دیتابیس موجود (اگر وجود دارد)
if exist instance\cms.db (
    echo 💾 ایجاد بکاپ از دیتابیس موجود...
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
    set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
    set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
    copy instance\cms.db backups\cms_backup_%timestamp%.db
)

REM متوقف کردن containerهای موجود
echo ⏹️ متوقف کردن containerهای موجود...
docker-compose -f %DOCKER_COMPOSE_FILE% down

REM حذف imageهای قدیمی (اختیاری)
echo 🧹 پاکسازی imageهای قدیمی...
docker image prune -f

REM ساخت و اجرای containerها
echo 🔨 ساخت و اجرای containerها...
docker-compose -f %DOCKER_COMPOSE_FILE% build --no-cache
docker-compose -f %DOCKER_COMPOSE_FILE% up -d

REM انتظار برای آماده شدن سرویس‌ها
echo ⏳ انتظار برای آماده شدن سرویس‌ها...
timeout /t 30 /nobreak >nul

REM بررسی وضعیت سرویس‌ها
echo 🔍 بررسی وضعیت سرویس‌ها...
docker-compose -f %DOCKER_COMPOSE_FILE% ps

REM بررسی health check
echo 🏥 بررسی health check...
for /l %%i in (1,1,10) do (
    curl -f http://localhost/health >nul 2>&1
    if not errorlevel 1 (
        echo ✅ سرویس‌ها با موفقیت راه‌اندازی شدند!
        goto :success
    ) else (
        echo ⏳ انتظار... (%%i/10)
        timeout /t 10 /nobreak >nul
    )
)

:success
echo.
echo 🎉 Deployment با موفقیت تکمیل شد!
echo.
echo 📊 اطلاعات دسترسی:
echo    🌐 وب سایت: http://localhost
echo    🔧 pgAdmin: http://localhost:8080
echo    📊 Health Check: http://localhost/health
echo.
echo 👤 اطلاعات ورود پیش‌فرض:
echo    نام کاربری: admin
echo    رمز عبور: admin123
echo.
echo 📋 دستورات مفید:
echo    مشاهده لاگ‌ها: docker-compose logs -f
echo    متوقف کردن: docker-compose down
echo    راه‌اندازی مجدد: docker-compose up -d
echo    بکاپ دیتابیس: docker-compose exec db pg_dump -U cms_user cms_db ^> backup.sql
echo.

pause

