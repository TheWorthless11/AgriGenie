param(
    [switch]$RemoveVolumes
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$TunnelPidFile = Join-Path $RuntimeDir "cloudflared.pid"
$PublicUrlFile = Join-Path $RuntimeDir "public_url.txt"
$GoogleRedirectUriFile = Join-Path $RuntimeDir "google_redirect_uri.txt"
$ProjectPublicUrlFile = Join-Path $RepoRoot "public_url.txt"
$ProjectGoogleRedirectUriFile = Join-Path $RepoRoot "google_redirect_uri.txt"

function Write-Step {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

Push-Location $RepoRoot
try {
    Write-Step "Stopping tracked Cloudflare tunnel process (if running)..."
    if (Test-Path $TunnelPidFile) {
        $pidText = (Get-Content -Path $TunnelPidFile -Raw).Trim()
        if ($pidText) {
            $trackedPid = 0
            if ([int]::TryParse($pidText, [ref]$trackedPid)) {
                $proc = Get-Process -Id $trackedPid -ErrorAction SilentlyContinue
                if ($proc) {
                    Stop-Process -Id $trackedPid -Force -ErrorAction SilentlyContinue
                }
            }
        }
        Remove-Item $TunnelPidFile -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $PublicUrlFile) {
        Remove-Item $PublicUrlFile -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $GoogleRedirectUriFile) {
        Remove-Item $GoogleRedirectUriFile -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $ProjectPublicUrlFile) {
        Remove-Item $ProjectPublicUrlFile -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $ProjectGoogleRedirectUriFile) {
        Remove-Item $ProjectGoogleRedirectUriFile -Force -ErrorAction SilentlyContinue
    }

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "Docker CLI not found. Tunnel has been stopped; skipping Docker shutdown." -ForegroundColor Yellow
        exit 0
    }

    $null = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker daemon is not running. Tunnel has been stopped; Docker stack may already be down." -ForegroundColor Yellow
        exit 0
    }

    Write-Step "Stopping Docker services..."
    $composeArgs = @("compose", "down")
    if ($RemoveVolumes) {
        $composeArgs += "--volumes"
    }

    docker @composeArgs

    Write-Host ""
    Write-Host "AgriGenie self-host stack stopped."
}
finally {
    Pop-Location
}
