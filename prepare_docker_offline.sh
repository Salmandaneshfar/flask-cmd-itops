#!/bin/bash
# اسکریپت آماده‌سازی Docker images برای نصب آفلاین

set -e

echo "=========================================="
echo "Flask CMS iTop - Docker Offline Preparation"
echo "=========================================="

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo "=== Step 1: Building Docker images ==="
docker compose build

echo ""
echo "=== Step 2: Exporting Docker images ==="
# دریافت نام image ها از docker-compose
WEB_IMAGE=$(docker compose config | grep -A 5 "web:" | grep "image:" | awk '{print $2}' | head -1)
NGINX_IMAGE=$(docker compose config | grep -A 5 "nginx:" | grep "image:" | awk '{print $2}' | head -1)

# اگر image نام مشخصی ندارند، از نام پروژه استفاده می‌کنیم
if [ -z "$WEB_IMAGE" ]; then
    WEB_IMAGE="flask-cms-itop-web"
fi
if [ -z "$NGINX_IMAGE" ]; then
    NGINX_IMAGE="flask-cms-itop-nginx"
fi

# ساخت image ها اگر وجود ندارند
if ! docker images | grep -q "$WEB_IMAGE"; then
    echo "Building web image..."
    docker compose build web
fi

if ! docker images | grep -q "$NGINX_IMAGE"; then
    echo "Building nginx image..."
    docker compose build nginx
fi

# Export images
echo ""
echo "=== Exporting images ==="
docker save "$WEB_IMAGE" "$NGINX_IMAGE" -o "flask-cms-itop-docker-images-${TIMESTAMP}.tar"

echo ""
echo "=========================================="
echo "Docker images exported: flask-cms-itop-docker-images-${TIMESTAMP}.tar"
echo "=========================================="
echo ""
echo "Image size: $(du -h flask-cms-itop-docker-images-${TIMESTAMP}.tar | cut -f1)"
echo ""
echo "To deploy on offline server:"
echo "  1. Transfer flask-cms-itop-docker-images-${TIMESTAMP}.tar to the server"
echo "  2. Load images: docker load < flask-cms-itop-docker-images-${TIMESTAMP}.tar"
echo "  3. Copy project files to /opt/flask-cms-itop"
echo "  4. Create .env.docker file"
echo "  5. Run: docker compose up -d"
echo ""

