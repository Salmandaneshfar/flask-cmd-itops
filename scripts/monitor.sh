#!/bin/bash

# اسکریپت مانیتورینگ سیستم
# استفاده: ./monitor.sh

set -e

DOCKER_COMPOSE_FILE="docker-compose.yml"

echo "📊 مانیتورینگ سیستم Flask CMS"
echo "================================"

# بررسی وضعیت containerها
echo "🐳 وضعیت Containerها:"
docker-compose -f $DOCKER_COMPOSE_FILE ps

echo ""

# بررسی استفاده از منابع
echo "💾 استفاده از منابع:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

echo ""

# بررسی لاگ‌های اخیر
echo "📝 لاگ‌های اخیر (آخرین 10 خط):"
docker-compose -f $DOCKER_COMPOSE_FILE logs --tail=10

echo ""

# بررسی health check
echo "🏥 Health Check:"
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ سیستم سالم است"
    curl -s http://localhost/health | jq '.' 2>/dev/null || curl -s http://localhost/health
else
    echo "❌ سیستم مشکل دارد"
fi

echo ""

# بررسی فضای دیسک
echo "💽 فضای دیسک:"
df -h

echo ""

# بررسی حافظه
echo "🧠 وضعیت حافظه:"
free -h

echo ""

# بررسی لاگ‌های امنیت
if [ -f "logs/security.log" ]; then
    echo "🔒 آخرین رویدادهای امنیتی:"
    tail -5 logs/security.log
fi







