# Inline deployment script - executes commands directly via SSH
$server = "188.121.105.3"
$user = "rocky"
$password = "admin@123"

Write-Host "=========================================="
Write-Host "Flask CMS iTop - Automated Deployment"
Write-Host "Server: $user@$server"
Write-Host "=========================================="
Write-Host ""

# Commands to execute on remote server (using here-string with proper escaping)
$remoteCommands = 'cd /opt/flask-cms-itop && git pull && chmod +x deploy_rocky.sh && ./deploy_rocky.sh'

Write-Host "Executing deployment commands on remote server..."
Write-Host "Note: You will be prompted for password: $password"
Write-Host ""

# Use WSL to execute ssh with sshpass
$wslScript = "#!/bin/bash`n" + 
             "export DEBIAN_FRONTEND=noninteractive`n" +
             "if ! command -v sshpass &> /dev/null; then`n" +
             "  echo 'Installing sshpass...'`n" +
             "  sudo apt-get update -qq > /dev/null 2>&1`n" +
             "  sudo apt-get install -y -qq sshpass > /dev/null 2>&1`n" +
             "fi`n" +
             "sshpass -p '$password' ssh -o StrictHostKeyChecking=no $user@$server '$remoteCommands'`n"

$wslScript | Out-File -FilePath deploy_wsl.sh -Encoding ASCII -NoNewline
wsl bash -c "dos2unix deploy_wsl.sh 2>/dev/null || sed -i 's/\r$//' deploy_wsl.sh; bash deploy_wsl.sh"
Remove-Item deploy_wsl.sh -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Deployment completed!"

