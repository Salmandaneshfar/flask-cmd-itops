#!/bin/bash
set -e

echo "=========================================="
echo "Flask CMS iTop - Deployment Script"
echo "Rocky Linux 8.5"
echo "=========================================="

cd /opt/flask-cms-itop

echo ""
echo "=== Step 1: Pulling latest changes ==="
git pull

echo ""
echo "=== Step 2: Creating .env.docker file ==="
if [ ! -f docker/env.docker.sample ]; then
    echo "ERROR: docker/env.docker.sample not found!"
    exit 1
fi
cp docker/env.docker.sample .env.docker

echo ""
echo "=== Step 3: Generating SECRET_KEY ==="
if command -v python3 &> /dev/null; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env.docker
    echo "SECRET_KEY generated and updated in .env.docker"
else
    echo "WARNING: python3 not found, using openssl"
    SECRET_KEY=$(openssl rand -base64 32 | tr -d '\n')
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env.docker
    echo "SECRET_KEY generated using openssl"
fi

echo ""
echo "=== Step 4: Generating CREDENTIALS_KEY ==="
if command -v python3 &> /dev/null; then
    # Check if cryptography is available
    if python3 -c "from cryptography.fernet import Fernet" 2>/dev/null; then
        CREDENTIALS_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        sed -i "s|CREDENTIALS_KEY=.*|CREDENTIALS_KEY=$CREDENTIALS_KEY|g" .env.docker
        echo "CREDENTIALS_KEY generated and updated in .env.docker"
    else
        echo "WARNING: cryptography module not found"
        echo "Please install it: pip3 install cryptography"
        echo "Or generate key manually and update .env.docker"
    fi
else
    echo "WARNING: python3 not found"
    echo "Please generate CREDENTIALS_KEY manually using:"
    echo "  docker run --rm python:3.11-slim python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
fi

echo ""
echo "=== Step 5: Building Docker images ==="
docker compose build

echo ""
echo "=== Step 6: Starting containers ==="
docker compose up -d

echo ""
echo "=== Step 7: Container status ==="
sleep 3
docker compose ps

echo ""
echo "=== Step 8: Viewing recent logs ==="
docker compose logs --tail=50 flask

echo ""
echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo ""
echo "To view logs: docker compose logs -f flask"
echo "To stop: docker compose down"
echo "To restart: docker compose restart"


