# استفاده از Python 3.11 slim روی Debian Bookworm (پایدارتر از trixie)
FROM python:3.11-slim-bookworm

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# ایجاد کاربر غیر root برای امنیت
RUN groupadd -r appuser && useradd -r -g appuser appuser

# نصب وابستگی‌های سیستم با منطق retry برای پایدارسازی build
RUN set -eux; \
    echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/80retries; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates; \
    update-ca-certificates; \
    for i in 1 2 3 4 5; do \
        apt-get update && \
        apt-get install -y --no-install-recommends \
            build-essential \
            libpq-dev \
            postgresql-client \
        && break || sleep 5; \
    done; \
    rm -rf /var/lib/apt/lists/*

# تنظیم دایرکتوری کار
WORKDIR /app

# کپی فایل requirements و نصب وابستگی‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# کپی کد برنامه
COPY . .

# ایجاد دایرکتوری‌های مورد نیاز
RUN mkdir -p /app/instance /app/static/uploads /app/logs && \
    chown -R appuser:appuser /app

# تغییر مالکیت فایل‌ها
RUN chown -R appuser:appuser /app

# تغییر به کاربر غیر root
USER appuser

# پورت داخلی
EXPOSE 5000

# Health check (use Python instead of curl)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; from urllib.error import URLError; url='http://localhost:5000/health'; \
try: \
    resp=urllib.request.urlopen(url, timeout=10); \
    sys.exit(0 if resp.getcode()==200 else 1) \
except URLError: \
    sys.exit(1)"

# اجرای برنامه
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]

