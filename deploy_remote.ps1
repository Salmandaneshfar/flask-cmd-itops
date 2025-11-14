# PowerShell script to deploy to remote server
# This script uses plink (PuTTY) if available, otherwise provides manual instructions

$server = "188.121.105.3"
$user = "rocky"
$password = "admin@123"
$remotePath = "/opt/flask-cms-itop"

Write-Host "=========================================="
Write-Host "Flask CMS iTop - Remote Deployment"
Write-Host "Server: $server"
Write-Host "=========================================="
Write-Host ""

# Check if plink is available
$plinkPath = Get-Command plink -ErrorAction SilentlyContinue

if ($plinkPath) {
    Write-Host "Using plink for automated deployment..."
    
    # Create a command file for plink
    $commands = @"
cd $remotePath
git pull
chmod +x deploy_rocky.sh
./deploy_rocky.sh
"@
    
    $commands | Out-File -FilePath deploy_commands.txt -Encoding ASCII
    
    # Execute using plink
    $plinkArgs = "-ssh", "$user@$server", "-pw", $password, "-m", "deploy_commands.txt"
    & plink $plinkArgs
    
    Remove-Item deploy_commands.txt -ErrorAction SilentlyContinue
} else {
    Write-Host "plink not found. Please install PuTTY or use manual method."
    Write-Host ""
    Write-Host "Manual deployment steps:"
    Write-Host "1. Connect to server: ssh $user@$server"
    Write-Host "2. Run: cd $remotePath"
    Write-Host "3. Run: git pull"
    Write-Host "4. Run: chmod +x deploy_rocky.sh"
    Write-Host "5. Run: ./deploy_rocky.sh"
    Write-Host ""
    Write-Host "Or install PuTTY and run this script again."
}


