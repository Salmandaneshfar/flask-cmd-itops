#!/bin/bash
# بسته‌بندی سریع فایل‌های پروژه برای انتقال آفلاین

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="flask-cms-itop-simple-${TIMESTAMP}.tar.gz"

echo "=========================================="
echo "Flask CMS iTop - Simple Package"
echo "=========================================="
echo ""

echo "Creating archive: $ARCHIVE_NAME"
tar -czf "$ARCHIVE_NAME" \
    --exclude='.git' \
    --exclude='.venv*' \
    --exclude='venv*' \
    --exclude='instance/*.db' \
    --exclude='instance/*.db-journal' \
    --exclude='logs/*' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='.env.docker' \
    --exclude='*.log' \
    --exclude='static/uploads/*' \
    --exclude='flask-cms-itop-offline' \
    --exclude='flask-cms-itop-*.tar.gz' \
    --exclude='*.tar.gz' \
    .

echo ""
echo "=========================================="
echo "Package created: $ARCHIVE_NAME"
echo "=========================================="
echo ""
echo "Size: $(du -h "$ARCHIVE_NAME" | cut -f1)"
echo ""
echo "To deploy:"
echo "  1. Transfer $ARCHIVE_NAME to server"
echo "  2. Extract: tar -xzf $ARCHIVE_NAME"
echo "  3. Follow OFFLINE_DEPLOYMENT.md instructions"
echo ""

