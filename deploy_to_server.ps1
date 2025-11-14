$password = ConvertTo-SecureString "admin@123" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential("rocky", $password)

$server = "188.121.105.3"
$commands = @(
    "cd /opt/flask-cms-itop",
    "git pull",
    "cp docker/env.docker.sample .env.docker",
    "python3 -c `"import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))`" > /tmp/secret_key.txt",
    "python3 -c `"from cryptography.fernet import Fernet; print('CREDENTIALS_KEY=' + Fernet.generate_key().decode())`" > /tmp/creds_key.txt",
    "SECRET_KEY=`$(cat /tmp/secret_key.txt)",
    "CREDENTIALS_KEY=`$(cat /tmp/creds_key.txt)",
    "sed -i 's|SECRET_KEY=.*|'`$SECRET_KEY'|g' .env.docker",
    "sed -i 's|CREDENTIALS_KEY=.*|'`$CREDENTIALS_KEY'|g' .env.docker",
    "docker compose build",
    "docker compose up -d",
    "docker compose ps"
)

$scriptBlock = {
    param($cmds)
    $allCommands = $cmds -join " && "
    Invoke-Expression $allCommands
}

Write-Host "Connecting to server and executing commands..."
Invoke-Command -ComputerName $server -Credential $credential -ScriptBlock $scriptBlock -ArgumentList $commands


