#!/bin/bash
# اسکریپت آماده‌سازی برای نصب آفلاین
# این اسکریپت باید در محیط با اینترنت اجرا شود

set -e

echo "=========================================="
echo "Flask CMS iTop - Offline Package Preparation"
echo "=========================================="

PROJECT_DIR=$(pwd)
OFFLINE_DIR="flask-cms-itop-offline"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo "=== Step 1: Creating offline package directory ==="
rm -rf "$OFFLINE_DIR"
mkdir -p "$OFFLINE_DIR"

echo ""
echo "=== Step 2: Copying project files ==="
# کپی فایل‌های پروژه (بدون .git, .venv, instance, logs)
rsync -av --exclude='.git' \
          --exclude='.venv' \
          --exclude='instance/*.db' \
          --exclude='instance/*.db-journal' \
          --exclude='logs/*' \
          --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='.env' \
          --exclude='.env.docker' \
          --exclude='*.log' \
          --exclude='static/uploads/*' \
          . "$OFFLINE_DIR/"

echo ""
echo "=== Step 3: Downloading Python wheel files ==="
mkdir -p "$OFFLINE_DIR/wheels"
if command -v pip &> /dev/null; then
    echo "Downloading wheels for offline installation..."
    pip download -r requirements.txt -d "$OFFLINE_DIR/wheels" || echo "Warning: Some packages may not be available as wheels"
    pip wheel -r requirements.txt -w "$OFFLINE_DIR/wheels" || echo "Warning: Some packages failed to build as wheels"
else
    echo "Warning: pip not found, skipping wheel download"
fi

echo ""
echo "=== Step 4: Creating installation script ==="
cat > "$OFFLINE_DIR/install_offline.sh" <<'INSTALL_EOF'
#!/bin/bash
# اسکریپت نصب آفلاین

set -e

echo "=========================================="
echo "Flask CMS iTop - Offline Installation"
echo "=========================================="

# بررسی Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found!"
    exit 1
fi

# ساخت venv
echo ""
echo "=== Creating virtual environment ==="
python3 -m venv .venv
source .venv/bin/activate

# نصب pip
echo ""
echo "=== Upgrading pip ==="
pip install --upgrade pip wheel setuptools

# نصب پکیج‌ها از wheels
echo ""
echo "=== Installing packages from wheels ==="
if [ -d "wheels" ] && [ "$(ls -A wheels)" ]; then
    pip install --no-index --find-links ./wheels -r requirements.txt
else
    echo "Warning: No wheels directory found, trying to install from PyPI (requires internet)"
    pip install -r requirements.txt
fi

# ساخت دایرکتوری‌ها
echo ""
echo "=== Creating directories ==="
mkdir -p instance static/uploads logs

# ساخت .env
echo ""
echo "=== Creating .env file ==="
if [ ! -f .env ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    CREDENTIALS_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    cat > .env <<EOF
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY
CREDENTIALS_KEY=$CREDENTIALS_KEY
UPLOAD_FOLDER=static/uploads
DATABASE_URL=sqlite:///instance/cms.db
EOF
    echo ".env file created"
fi

# راه‌اندازی دیتابیس
echo ""
echo "=== Setting up database ==="
flask db upgrade || python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"

echo ""
echo "=========================================="
echo "Installation completed!"
echo "=========================================="
echo ""
echo "To run the application:"
echo "  source .venv/bin/activate"
echo "  gunicorn -c gunicorn.conf.py wsgi:application"
INSTALL_EOF

chmod +x "$OFFLINE_DIR/install_offline.sh"

echo ""
echo "=== Step 5: Creating archive ==="
ARCHIVE_NAME="flask-cms-itop-offline-${TIMESTAMP}.tar.gz"
tar -czf "$ARCHIVE_NAME" "$OFFLINE_DIR"

echo ""
echo "=========================================="
echo "Offline package created: $ARCHIVE_NAME"
echo "=========================================="
echo ""
echo "Package size: $(du -h "$ARCHIVE_NAME" | cut -f1)"
echo ""
echo "To deploy on offline server:"
echo "  1. Transfer $ARCHIVE_NAME to the server"
echo "  2. Extract: tar -xzf $ARCHIVE_NAME"
echo "  3. Run: cd $OFFLINE_DIR && ./install_offline.sh"
echo ""

