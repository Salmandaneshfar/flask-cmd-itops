# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/auto-commit.ps1
param(
    [int]$IntervalSeconds = 30,
    [string]$Branch = "main"
)

Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) | Out-Null
Set-Location -Path (Resolve-Path ..) | Out-Null

function Get-RepoRoot {
    $p = (git rev-parse --show-toplevel) 2>$null
    if (-not $p) { throw "Not a git repository" }
    return $p.Trim()
}

$repo = Get-RepoRoot
Set-Location $repo

Write-Host "Auto-commit running in $repo (branch: $Branch), interval: $IntervalSeconds sec"

while ($true) {
    try {
        $status = git status --porcelain
        if ($LASTEXITCODE -ne 0) { Start-Sleep -Seconds $IntervalSeconds; continue }
        if ($status) {
            git add -A | Out-Null
            $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            git commit -m "auto: save at $ts" | Out-Null
            git push origin $Branch | Out-Null
            Write-Host "[$ts] Changes committed and pushed"
        }
    } catch {
        Write-Warning $_
    }
    Start-Sleep -Seconds $IntervalSeconds
}
