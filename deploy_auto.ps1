$password = "admin@123"
$server = "188.121.105.3"
$user = "rocky"

# Create a here-document style script
$scriptContent = @"
#!/bin/bash
set -e
cd /opt/flask-cms-itop
echo "=== Pulling latest changes ==="
git pull
echo "=== Creating .env.docker file ==="
cp docker/env.docker.sample .env.docker
echo "=== Generating SECRET_KEY ==="
SECRET_KEY=\$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i "s|SECRET_KEY=.*|SECRET_KEY=\$SECRET_KEY|g" .env.docker
echo "=== Generating CREDENTIALS_KEY ==="
CREDENTIALS_KEY=\$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
sed -i "s|CREDENTIALS_KEY=.*|CREDENTIALS_KEY=\$CREDENTIALS_KEY|g" .env.docker
echo "=== Building Docker images ==="
docker compose build
echo "=== Starting containers ==="
docker compose up -d
echo "=== Container status ==="
docker compose ps
echo "=== Viewing logs ==="
docker compose logs --tail=50 flask
echo "=== Deployment completed! ==="
"@

# Write script to temp file
$scriptContent | Out-File -FilePath deploy_temp.sh -Encoding utf8 -NoNewline

Write-Host "Uploading script to server..."
# Use ssh with password via expect-like approach
# Since we can't use expect, we'll use a different method

# Try using ssh with a here-document
$commands = @"
cd /opt/flask-cms-itop
git pull
cp docker/env.docker.sample .env.docker
SECRET_KEY=\$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i "s|SECRET_KEY=.*|SECRET_KEY=\$SECRET_KEY|g" .env.docker
CREDENTIALS_KEY=\$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
sed -i "s|CREDENTIALS_KEY=.*|CREDENTIALS_KEY=\$CREDENTIALS_KEY|g" .env.docker
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=50 flask
"@

Write-Host "Please run the following command manually:"
Write-Host "ssh $user@$server"
Write-Host "Then execute:"
Write-Host $commands


