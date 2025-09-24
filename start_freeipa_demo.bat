@echo off
echo Starting FreeIPA Demo Server...

REM Stop existing container
docker stop freeipa-server 2>nul
docker rm freeipa-server 2>nul

REM Start FreeIPA server
echo Starting FreeIPA container...
docker run -d ^
  --name freeipa-server ^
  --hostname ipa.example.com ^
  -p 80:80 ^
  -p 443:443 ^
  -p 389:389 ^
  -p 636:636 ^
  -e IPA_SERVER_IP=127.0.0.1 ^
  -e PASSWORD=MySecretPassword123 ^
  --sysctl net.ipv6.conf.all.disable_ipv6=0 ^
  --privileged ^
  freeipa/freeipa-server:latest

echo.
echo FreeIPA server is starting...
echo Please wait 2-3 minutes for the server to be ready
echo.
echo Web UI: http://localhost
echo Admin: admin / MySecretPassword123
echo.
echo Press any key to continue...
pause >nul








