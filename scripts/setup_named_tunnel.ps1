param(
    [string]$TunnelName = '',
    [string]$Hostname = '',
    [switch]$OverwriteDns,
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RepoRoot '.env'
$RuntimeDir = Join-Path $RepoRoot '.runtime'
$PublicUrlFile = Join-Path $RuntimeDir 'public_url.txt'

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

function Set-EnvValue {
    param(
        [string]$Path,
        [string]$Name,
        [string]$Value
    )

    $lines = @()
    if (Test-Path $Path) {
        $lines = Get-Content -Path $Path
    }

    $pattern = "^$([regex]::Escape($Name))="
    $replacement = "$Name=$Value"
    $updated = $false

    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match $pattern) {
            $lines[$i] = $replacement
            $updated = $true
            break
        }
    }

    if (-not $updated) {
        $lines += $replacement
    }

    Set-Content -Path $Path -Value $lines -Encoding UTF8
}

function Merge-CsvValue {
    param(
        [string]$Csv,
        [string]$Value
    )

    $items = @()
    if ($Csv) {
        $items = $Csv.Split(',') |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
    }

    if ($items -notcontains $Value) {
        $items += $Value
    }

    return ($items -join ',')
}

$script:OriginCertPath = ''

function Invoke-CloudflaredManagement {
    param(
        [string[]]$Args,
        [switch]$AllowFailure
    )

    $commandArgs = @('tunnel')
    if ($script:OriginCertPath) {
        $commandArgs += @('--origincert', $script:OriginCertPath)
    }
    $commandArgs += $Args

    $output = & cloudflared @commandArgs 2>&1
    $exitCode = $LASTEXITCODE
    $outputText = ($output | Out-String).Trim()

    if (-not $AllowFailure -and $exitCode -ne 0) {
        Fail "cloudflared command failed: cloudflared $($commandArgs -join ' ')`n$outputText"
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        OutputText = $outputText
    }
}

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Fail 'cloudflared is not installed. Install it with: winget install --id Cloudflare.cloudflared -e'
}

if (-not $TunnelName) {
    $TunnelName = (Get-EnvValue -Path $EnvFile -Name 'CLOUDFLARE_TUNNEL_NAME')
}
if (-not $TunnelName) {
    $TunnelName = 'agrigenie'
}

if (-not $Hostname) {
    $Hostname = (Get-EnvValue -Path $EnvFile -Name 'CLOUDFLARE_TUNNEL_HOSTNAME')
}
if (-not $Hostname) {
    Fail 'Provide a stable hostname from your Cloudflare domain using -Hostname (example: app.yourdomain.com).'
}

if ($Hostname -match '^https?://') {
    Fail "Hostname must not include protocol. Use only host name, for example: app.yourdomain.com"
}

if ($Hostname -notmatch '^[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}$') {
    Fail "Hostname '$Hostname' is not a valid full domain name. Use a value like app.yourdomain.com under a Cloudflare-managed domain."
}

$originFromEnv = (Get-EnvValue -Path $EnvFile -Name 'CLOUDFLARE_TUNNEL_ORIGIN_CERT')
if ($originFromEnv) {
    $script:OriginCertPath = $originFromEnv
} else {
    $script:OriginCertPath = Join-Path $HOME '.cloudflared\cert.pem'
}

if (-not (Test-Path $script:OriginCertPath)) {
    Write-Step 'Cloudflare origin cert not found. Opening browser login for one-time authorization...'
    cloudflared tunnel login
    if ($LASTEXITCODE -ne 0) {
        Fail 'cloudflared tunnel login failed.'
    }

    $defaultCert = Join-Path $HOME '.cloudflared\cert.pem'
    if (-not (Test-Path $defaultCert)) {
        Fail 'Login completed but cert.pem was not found. Run cloudflared tunnel login manually and retry.'
    }

    $script:OriginCertPath = $defaultCert
}

Write-Step "Checking named tunnel '$TunnelName'..."
$listResult = Invoke-CloudflaredManagement -Args @('list', '--output', 'json', '--name', $TunnelName)
$tunnels = @()
if ($listResult.OutputText) {
    $parsed = $listResult.OutputText | ConvertFrom-Json
    $tunnels = @($parsed)
}

if ($tunnels.Count -eq 0) {
    Write-Step "Creating named tunnel '$TunnelName'..."
    $createResult = Invoke-CloudflaredManagement -Args @('create', $TunnelName)
    Write-Host $createResult.OutputText

    $listResult = Invoke-CloudflaredManagement -Args @('list', '--output', 'json', '--name', $TunnelName)
    if ($listResult.OutputText) {
        $parsed = $listResult.OutputText | ConvertFrom-Json
        $tunnels = @($parsed)
    }
}

if ($tunnels.Count -eq 0) {
    Fail "Tunnel '$TunnelName' could not be found after creation attempt."
}

$tunnelId = $tunnels[0].id
$credentialsFile = Join-Path $HOME ".cloudflared\$tunnelId.json"
if (-not (Test-Path $credentialsFile)) {
    Fail "Tunnel credentials file not found: $credentialsFile"
}

Write-Step "Routing DNS for $Hostname to tunnel $tunnelId..."
$routeArgs = @('route', 'dns')
if ($OverwriteDns) {
    $routeArgs += '--overwrite-dns'
}
$routeArgs += @($tunnelId, $Hostname)
$routeResult = Invoke-CloudflaredManagement -Args $routeArgs -AllowFailure

if ($routeResult.ExitCode -ne 0) {
    if ($routeResult.OutputText -match 'already exists|already routed') {
        Write-Host '[*] DNS record already points to this tunnel.' -ForegroundColor Yellow
    } else {
        Fail "DNS route failed: $($routeResult.OutputText)"
    }
}

if (-not (Test-Path $EnvFile)) {
    New-Item -Path $EnvFile -ItemType File | Out-Null
}

Set-EnvValue -Path $EnvFile -Name 'CLOUDFLARE_TUNNEL_MODE' -Value 'named'
Set-EnvValue -Path $EnvFile -Name 'CLOUDFLARE_TUNNEL_NAME' -Value $TunnelName
Set-EnvValue -Path $EnvFile -Name 'CLOUDFLARE_TUNNEL_ID' -Value $tunnelId
Set-EnvValue -Path $EnvFile -Name 'CLOUDFLARE_TUNNEL_CREDENTIALS_FILE' -Value $credentialsFile
Set-EnvValue -Path $EnvFile -Name 'CLOUDFLARE_TUNNEL_HOSTNAME' -Value $Hostname
Set-EnvValue -Path $EnvFile -Name 'CLOUDFLARE_TUNNEL_ORIGIN_CERT' -Value $script:OriginCertPath

$hosts = Get-EnvValue -Path $EnvFile -Name 'ALLOWED_HOSTS'
if (-not $hosts) {
    $hosts = 'localhost,127.0.0.1,.trycloudflare.com'
}
$hosts = Merge-CsvValue -Csv $hosts -Value $Hostname
Set-EnvValue -Path $EnvFile -Name 'ALLOWED_HOSTS' -Value $hosts

$csrfOrigins = Get-EnvValue -Path $EnvFile -Name 'CSRF_TRUSTED_ORIGINS'
if (-not $csrfOrigins) {
    $csrfOrigins = 'https://*.trycloudflare.com'
}
$csrfOrigins = Merge-CsvValue -Csv $csrfOrigins -Value "https://$Hostname"
Set-EnvValue -Path $EnvFile -Name 'CSRF_TRUSTED_ORIGINS' -Value $csrfOrigins

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
Set-Content -Path $PublicUrlFile -Value "https://$Hostname" -NoNewline

$callbackUri = "https://$Hostname/accounts/google/login/callback/"

Write-Host ''
Write-Host '================================================'
Write-Host ' Named Cloudflare tunnel is configured'
Write-Host '================================================'
Write-Host "Tunnel Name : $TunnelName"
Write-Host "Tunnel ID   : $tunnelId"
Write-Host "Public URL  : https://$Hostname"
Write-Host 'Google OAuth Redirect URI (add in Google Console):'
Write-Host $callbackUri
Write-Host ''
Write-Host 'Next:'
Write-Host '1. Add the redirect URI above in Google Cloud Console OAuth credentials.'
Write-Host '2. Restart app with .\start_zero_cost.bat'
Write-Host "3. Verify login at https://$Hostname/auth/google/"
