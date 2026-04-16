param(
    [int]$Port = 8000,
    [switch]$OpenBrowser,
    [ValidateSet('quick', 'named')]
    [string]$TunnelMode = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot '.env'
$RuntimeDir = Join-Path $RepoRoot ".runtime"
$TunnelLog = Join-Path $RuntimeDir "cloudflared.log"
$TunnelPidFile = Join-Path $RuntimeDir "cloudflared.pid"
$PublicUrlFile = Join-Path $RuntimeDir "public_url.txt"
$GoogleRedirectUriFile = Join-Path $RuntimeDir "google_redirect_uri.txt"
$ProjectPublicUrlFile = Join-Path $RepoRoot "public_url.txt"
$ProjectGoogleRedirectUriFile = Join-Path $RepoRoot "google_redirect_uri.txt"

function Write-Step {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

function Fail {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

function Get-EnvValue {
    param(
        [string]$Path,
        [string]$Name
    )

    if (-not (Test-Path $Path)) {
        return ''
    }

    $pattern = "^$([regex]::Escape($Name))=(.*)$"
    foreach ($line in Get-Content -Path $Path) {
        if ($line -match $pattern) {
            return $Matches[1].Trim()
        }
    }

    return ''
}

function Resolve-Setting {
    param(
        [string]$Name,
        [string]$Default = ''
    )

    $processValue = [Environment]::GetEnvironmentVariable($Name)
    if (-not [string]::IsNullOrWhiteSpace($processValue)) {
        return $processValue.Trim()
    }

    $fileValue = Get-EnvValue -Path $EnvFile -Name $Name
    if (-not [string]::IsNullOrWhiteSpace($fileValue)) {
        return $fileValue.Trim()
    }

    return $Default
}

$effectiveTunnelMode = if ($TunnelMode) {
    $TunnelMode.ToLowerInvariant()
} else {
    (Resolve-Setting -Name 'CLOUDFLARE_TUNNEL_MODE' -Default 'quick').ToLowerInvariant()
}

$effectiveCloudflaredProtocol = (Resolve-Setting -Name 'CLOUDFLARED_PROTOCOL' -Default 'http2').ToLowerInvariant()

if ($effectiveTunnelMode -notin @('quick', 'named')) {
    Fail "Invalid tunnel mode '$effectiveTunnelMode'. Use 'quick' or 'named'."
}

if ($effectiveCloudflaredProtocol -notin @('auto', 'quic', 'http2')) {
    Fail "Invalid CLOUDFLARED_PROTOCOL '$effectiveCloudflaredProtocol'. Use auto, quic, or http2."
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Fail "Docker CLI was not found. Install Docker Desktop first."
}

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Fail "cloudflared is not installed. Install it with: winget install --id Cloudflare.cloudflared -e"
}

Write-Step "Checking Docker daemon..."
$null = docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    Fail "Docker daemon is not running. Open Docker Desktop and wait for the engine to start, then rerun this script."
}

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

Write-Step "Stopping stale cloudflared process (if any)..."
if (Test-Path $TunnelPidFile) {
    $oldPidText = (Get-Content -Path $TunnelPidFile -Raw).Trim()
    if ($oldPidText) {
        $oldPid = 0
        if ([int]::TryParse($oldPidText, [ref]$oldPid)) {
            $oldProc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
            if ($oldProc) {
                Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
            }
        }
    }
    Remove-Item $TunnelPidFile -Force -ErrorAction SilentlyContinue
}

if (Test-Path $TunnelLog) {
    Remove-Item $TunnelLog -Force -ErrorAction SilentlyContinue
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

Push-Location $RepoRoot
try {
    $effectiveHosts = Resolve-Setting -Name 'ALLOWED_HOSTS'
    $effectiveCsrfOrigins = Resolve-Setting -Name 'CSRF_TRUSTED_ORIGINS'

    if ($effectiveTunnelMode -eq 'named') {
        $tunnelHostname = Resolve-Setting -Name 'CLOUDFLARE_TUNNEL_HOSTNAME'
        if (-not $tunnelHostname) {
            Fail "Named tunnel mode requires CLOUDFLARE_TUNNEL_HOSTNAME in .env"
        }

        if (-not $effectiveHosts) {
            $effectiveHosts = "localhost,127.0.0.1,web,.trycloudflare.com"
        }
        if (($effectiveHosts -split ',') -notcontains $tunnelHostname) {
            $effectiveHosts = "$effectiveHosts,$tunnelHostname"
        }

        $requiredOrigin = "https://$tunnelHostname"
        if (-not $effectiveCsrfOrigins) {
            $effectiveCsrfOrigins = "https://*.trycloudflare.com"
        }
        if (($effectiveCsrfOrigins -split ',') -notcontains $requiredOrigin) {
            $effectiveCsrfOrigins = "$effectiveCsrfOrigins,$requiredOrigin"
        }

        $env:ALLOWED_HOSTS = $effectiveHosts
        $env:CSRF_TRUSTED_ORIGINS = $effectiveCsrfOrigins
    }

    Write-Step "Starting AgriGenie stack (PostgreSQL, Redis, Django, Celery worker, Celery beat)..."
    docker compose up -d --build --remove-orphans
    if ($LASTEXITCODE -ne 0) {
        Fail "docker compose up failed. Review the compose logs and retry."
    }

    $publicUrl = $null
    if ($effectiveTunnelMode -eq 'named') {
        $tunnelId = Resolve-Setting -Name 'CLOUDFLARE_TUNNEL_ID'
        $credentialsFile = Resolve-Setting -Name 'CLOUDFLARE_TUNNEL_CREDENTIALS_FILE'
        $tunnelHostname = Resolve-Setting -Name 'CLOUDFLARE_TUNNEL_HOSTNAME'

        if (-not $tunnelId) {
            Fail "Named tunnel mode requires CLOUDFLARE_TUNNEL_ID in .env"
        }

        if (-not $credentialsFile) {
            $credentialsFile = Join-Path $HOME ".cloudflared\$tunnelId.json"
        }

        if (-not (Test-Path $credentialsFile)) {
            Fail "Tunnel credentials file not found: $credentialsFile. Run scripts/setup_named_tunnel.ps1 first."
        }

        Write-Step "Starting Cloudflare named tunnel in background..."
        $cfArgs = @(
            "tunnel",
            "run",
            "--url", "http://localhost:$Port",
            "--protocol", $effectiveCloudflaredProtocol,
            "--credentials-file", $credentialsFile,
            "--no-autoupdate",
            "--logfile", $TunnelLog,
            $tunnelId
        )

        $originCert = Resolve-Setting -Name 'CLOUDFLARE_TUNNEL_ORIGIN_CERT'
        if ($originCert) {
            $cfArgs = @("--origincert", $originCert) + $cfArgs
        }

        $cloudflaredProcess = Start-Process -FilePath "cloudflared" -ArgumentList $cfArgs -PassThru -WindowStyle Hidden
        Set-Content -Path $TunnelPidFile -Value $cloudflaredProcess.Id -NoNewline
        $publicUrl = "https://$tunnelHostname"
    } else {
        Write-Step "Starting Cloudflare quick tunnel in background..."
        $cfArgs = @(
            "tunnel",
            "--url", "http://localhost:$Port",
            "--protocol", $effectiveCloudflaredProtocol,
            "--no-autoupdate",
            "--logfile", $TunnelLog
        )
        $cloudflaredProcess = Start-Process -FilePath "cloudflared" -ArgumentList $cfArgs -PassThru -WindowStyle Hidden
        Set-Content -Path $TunnelPidFile -Value $cloudflaredProcess.Id -NoNewline

        for ($i = 0; $i -lt 60; $i++) {
            if (Test-Path $TunnelLog) {
                $matches = Select-String -Path $TunnelLog -Pattern 'https://[-a-z0-9]+\.trycloudflare\.com' -AllMatches -ErrorAction SilentlyContinue
                if ($matches) {
                    $lastMatch = $matches | Select-Object -Last 1
                    if ($lastMatch -and $lastMatch.Matches.Count -gt 0) {
                        $publicUrl = $lastMatch.Matches[0].Value
                        break
                    }
                }
            }
            Start-Sleep -Seconds 1
        }
    }

    $googleOrigin = $null
    $googleRedirectUri = $null
    if ($publicUrl) {
        $googleOrigin = $publicUrl.TrimEnd('/')
        $googleRedirectUri = "$googleOrigin/accounts/google/login/callback/"

        Set-Content -Path $PublicUrlFile -Value $publicUrl -NoNewline
        Set-Content -Path $ProjectPublicUrlFile -Value $publicUrl -NoNewline
        Set-Content -Path $GoogleRedirectUriFile -Value $googleRedirectUri -NoNewline
        Set-Content -Path $ProjectGoogleRedirectUriFile -Value $googleRedirectUri -NoNewline
    }

    Write-Host ""
    Write-Host "================================================"
    Write-Host " AgriGenie is running with zero-cost self-hosting"
    Write-Host "================================================"
    Write-Host "Local URL : http://localhost:$Port"
    if ($publicUrl) {
        Write-Host "Public URL: $publicUrl"
        Write-Host "Admin URL : $publicUrl/admin"
        Write-Host "Saved URL : $ProjectPublicUrlFile"
        Write-Host "Google Origin: $googleOrigin"
        Write-Host "Google Redirect URI: $googleRedirectUri"
        Write-Host "Saved Redirect URI: $ProjectGoogleRedirectUriFile"
        if ($effectiveTunnelMode -eq 'quick') {
            Write-Host "Note: Quick tunnel URL changes on restart. Update Google OAuth redirect URI after every restart." -ForegroundColor Yellow
        }
    } else {
        Write-Host "Public URL: Not detected yet. Check log: $TunnelLog"
    }
    Write-Host ""
    Write-Host "To stop everything: .\stop_zero_cost.bat"

    if ($OpenBrowser -and $publicUrl) {
        Start-Process $publicUrl | Out-Null
    }
}
finally {
    Pop-Location
}
