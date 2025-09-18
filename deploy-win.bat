@echo off
REM Wrapper to run PowerShell deployment for Windows Server
setlocal

set SCRIPT=deploy.ps1
set ENVFILE=production.env

if not exist "%SCRIPT%" (
  echo deploy.ps1 not found in current directory.
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -EnvFile "%ENVFILE%" %*

endlocal
