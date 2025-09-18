# PowerShell deployment script for Windows Server (Production via Docker Compose)
Param(
    [string]$EnvFile = "production.env",
    [switch]$WithPgAdmin,
    [switch]$WithBackup
)

$ErrorActionPreference = 'Stop'

Write-Host "Starting production deployment on Windows Server..." -ForegroundColor Cyan

# Ensure running from repo root
$repoMarkers = @('docker-compose.prod.yml','Dockerfile','README.md')
$here = Get-Location
foreach ($m in $repoMarkers) {
    if (-not (Test-Path -LiteralPath (Join-Path $here $m))) {
        Write-Error "Please run this script from the project root (missing $m)."
    }
}

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH."
}
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Error "Docker Compose is not installed or not in PATH."
}

# Create required directories
$dirs = @(
    'backups', 'logs', 'static/uploads', 'ssl', 'logs/nginx'
)
foreach ($d in $dirs) { if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null } }

# Ensure env file
if (-not (Test-Path -LiteralPath $EnvFile)) {
    if (Test-Path -LiteralPath 'production.env') { $EnvFile = 'production.env' }
    elseif (Test-Path -LiteralPath 'env.example') { Copy-Item 'env.example' $EnvFile }
    else { Write-Error "Environment file not found. Provide -EnvFile production.env" }
}

Write-Host "Using env file: $EnvFile" -ForegroundColor Yellow

# Optional self-signed cert generation if none present
$certPem = Join-Path (Get-Location) 'ssl/cert.pem'
$keyPem  = Join-Path (Get-Location) 'ssl/key.pem'
if (-not (Test-Path $certPem) -or -not (Test-Path $keyPem)) {
    Write-Host "Generating self-signed certificate (for testing)..." -ForegroundColor Yellow
    try {
        $cert = New-SelfSignedCertificate -DnsName 'localhost' -CertStoreLocation 'Cert:\LocalMachine\My' -KeyUsage DigitalSignature, KeyEncipherment -NotAfter (Get-Date).AddYears(1)
        $pwd = [System.Guid]::NewGuid().ToString()
        $secure = ConvertTo-SecureString -String $pwd -Force -AsPlainText
        $pfxPath = Join-Path $env:TEMP 'cms-cert.pfx'
        Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $secure | Out-Null
        # Requires OpenSSL for PEM export; skip if not present
        if (Get-Command openssl -ErrorAction SilentlyContinue) {
            & openssl pkcs12 -in $pfxPath -nodes -nocerts -passin pass:$pwd | Out-File -Encoding ascii $keyPem
            & openssl pkcs12 -in $pfxPath -clcerts -nokeys -passin pass:$pwd | Out-File -Encoding ascii $certPem
        } else {
            Write-Warning "OpenSSL not found. Place PEM files in ssl/ manually for HTTPS, or use HTTP via port 80."
        }
    } catch {
        Write-Warning "Failed to generate self-signed certificate: $($_.Exception.Message)"
    }
}

# Compose profiles
$profiles = @()
if ($WithPgAdmin) { $profiles += 'tools' }
if ($WithBackup)  { $profiles += 'backup' }

# Determine docker compose flavor (v2: docker compose, v1: docker-compose)
$useComposeV2 = $true
try { docker compose version | Out-Null } catch { $useComposeV2 = $false }

function Run-Compose {
    param(
        [Parameter(Mandatory=$true)][string[]]$Args
    )
    if ($useComposeV2) {
        & docker compose @Args
    } else {
        & docker-compose @Args
    }
}

# Build profile args array if needed
$profileArgs = @()
if ($profiles.Count -gt 0) {
    foreach ($p in $profiles) { $profileArgs += @('--profile', $p) }
}

# Stop any existing stack
Write-Host "Stopping existing containers..." -ForegroundColor DarkYellow
Run-Compose -Args @('-f','docker-compose.prod.yml','--env-file',$EnvFile,'down')

# Build and start
Write-Host "Building images..." -ForegroundColor DarkYellow
Run-Compose -Args @('-f','docker-compose.prod.yml','build','--no-cache')

Write-Host "Starting services..." -ForegroundColor DarkYellow
$upArgs = @('-f','docker-compose.prod.yml','--env-file',$EnvFile)
if ($profileArgs.Count -gt 0) { $upArgs += $profileArgs }
$upArgs += @('up','-d')
Run-Compose -Args $upArgs

# Wait and health check
Write-Host "Waiting for services to initialize..." -ForegroundColor DarkYellow
Start-Sleep -Seconds 25

Write-Host "Checking health endpoint..." -ForegroundColor DarkYellow
$ok = $false
for ($i=1; $i -le 10; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri 'http://localhost/health' -UseBasicParsing -TimeoutSec 10
        if ($resp.StatusCode -eq 200) { $ok = $true; break }
    } catch {}
    Start-Sleep -Seconds 6
}

if ($ok) {
    Write-Host "Deployment succeeded." -ForegroundColor Green
    Write-Host "Site: http://localhost"
    Write-Host "pgAdmin: http://localhost:8080 (if enabled)"
} else {
    Write-Warning 'Health check failed. Review logs with: docker compose logs -f (or docker-compose logs -f)'
}


