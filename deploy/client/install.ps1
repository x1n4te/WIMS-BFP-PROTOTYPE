<#
.SYNOPSIS
  Installs or updates WIMS-BFP from the offline bundle: verifies checksums, loads the images,
  prepares the certificate and configuration, starts the stack, waits for health, and creates
  the first administrator.
.DESCRIPTION
  Fresh install:  .\setup-secrets.ps1   then   .\install.ps1
  Update:         copy the new bundle over this folder (keep .env and certs\), then
                  .\install.ps1     (a backup is taken first when the stack is running)
  No internet is needed at any point.
#>
param(
    [string]$ImagesDir = (Join-Path $PSScriptRoot 'images'),
    [switch]$SkipChecksum,
    [switch]$SkipBackup,
    [string]$BackupDestination = 'C:\WIMS-Backups',
    [switch]$OpenFirewall
)

. "$PSScriptRoot\common.ps1"

Write-Step 'Pre-flight checks'
Assert-Docker
if (-not (Test-Path -LiteralPath $script:EnvFile)) { Fail 'No .env found. Run .\setup-secrets.ps1 first.' }
$cfg = Read-DotEnv
foreach ($k in 'WIMS_HOST', 'WIMS_SERVER_IP', 'POSTGRES_PASSWORD', 'WIMS_MASTER_KEY') {
    if (-not $cfg.ContainsKey($k) -or [string]::IsNullOrWhiteSpace($cfg[$k])) { Fail ".env is missing $k. Re-run setup-secrets.ps1 (-Force only on a brand-new install)." }
}
if ($cfg.WIMS_MASTER_KEY -match '^A+=*$') { Fail 'WIMS_MASTER_KEY is the all-zero placeholder. Generate a real key with setup-secrets.ps1.' }
foreach ($f in 'docker-compose.yml', 'nginx.conf', 'postgres-init', 'keycloak\bfp-realm.json', 'tools\bootstrap_admin.py') {
    if (-not (Test-Path -LiteralPath (Join-Path $script:Root $f))) { Fail "Bundle file missing: $f. The bundle is incomplete; copy it again." }
}

$stackRunning = ((Invoke-Quiet -Exe 'docker' -Arguments @('ps', '--filter', 'name=wims-postgres', '--format', '{{.Names}}')).Output -join '') -ne ''

# 1. Checksums ---------------------------------------------------------------------------------
$sums = Join-Path $ImagesDir 'SHA256SUMS.txt'
if (-not $SkipChecksum) {
    Write-Step 'Verifying bundle checksums (a few minutes for the large image file)'
    if (-not (Test-Path -LiteralPath $sums)) { Fail "SHA256SUMS.txt not found in $ImagesDir" }
    $bad = 0
    foreach ($line in [System.IO.File]::ReadAllLines($sums)) {
        if ($line.Trim() -eq '') { continue }
        $parts = $line -split '\s+', 2
        $file = Join-Path $script:Root ($parts[1].Trim().TrimStart('*'))
        if (-not (Test-Path -LiteralPath $file)) { Write-Host "  MISSING $($parts[1])" -ForegroundColor Red; $bad++; continue }
        if ((Get-FileSha256 $file) -ne $parts[0].ToLowerInvariant()) { Write-Host "  CORRUPT $($parts[1])" -ForegroundColor Red; $bad++ } else { Write-Host "  ok      $($parts[1])" }
    }
    if ($bad -gt 0) { Fail "$bad file(s) failed the checksum. Do not install; copy the bundle again from the original media." }
}

# 2. Safety backup before an update --------------------------------------------------------------
if ($stackRunning -and -not $SkipBackup) {
    Write-Step 'Existing installation found: taking a backup before updating'
    & "$PSScriptRoot\backup.ps1" -Destination $BackupDestination
}

# 3. Load images -----------------------------------------------------------------------------------
Write-Step 'Loading images (no internet needed)'
$tar = Join-Path $ImagesDir 'wims-images.tar'
if (-not (Test-Path -LiteralPath $tar)) { Fail "Image archive not found: $tar" }
Invoke-Native -Exe 'docker' -Arguments @('load', '-i', $tar)

# 4. Certificate -------------------------------------------------------------------------------------
if (-not (Test-Path -LiteralPath (Join-Path $script:Root 'certs\server\server.crt'))) {
    & "$PSScriptRoot\setup-certs.ps1"
}

# 5. Render runtime configuration ----------------------------------------------------------------------
Write-Step "Preparing configuration for $($cfg.WIMS_HOST)"
$runtime = Join-Path $script:Root 'runtime'
New-Item -ItemType Directory -Force -Path (Join-Path $runtime 'realm') | Out-Null
$keycloakDir = Join-Path $script:Root 'keycloak'
Invoke-Tool -Script 'render_realm.py' -ScriptArgs @('/kc/bfp-realm.json', '/out/bfp-realm.json', $cfg.WIMS_HOST) `
    -Mounts @('-v', "${keycloakDir}:/kc:ro", '-v', "$(Join-Path $runtime 'realm'):/out")

$nginx = [System.IO.File]::ReadAllText((Join-Path $script:Root 'nginx.conf'))
$nginx = $nginx.Replace('192.168.1.50', $cfg.WIMS_SERVER_IP).Replace('wims.bfp.lan', $cfg.WIMS_HOST)
[System.IO.File]::WriteAllText((Join-Path $runtime 'nginx.conf'), $nginx, (New-Object System.Text.UTF8Encoding($false)))

# 6. Start ---------------------------------------------------------------------------------------------------
Write-Step 'Starting WIMS-BFP (first start runs the database setup and can take several minutes)'
Invoke-Compose -Arguments @('up', '-d', '--remove-orphans', '--pull', 'never')

Write-Step 'Waiting for services to become healthy'
Wait-ContainersReady -Names @('wims-postgres', 'wims-redis', 'wims-keycloak', 'wims-backend', 'wims-celery-worker', 'wims-frontend', 'wims-nginx')

# 7. First administrator ---------------------------------------------------------------------------------------
$cfg = Read-DotEnv
if ($cfg.ContainsKey('BOOTSTRAP_ADMIN_PASSWORD') -and -not [string]::IsNullOrWhiteSpace($cfg.BOOTSTRAP_ADMIN_PASSWORD)) {
    Write-Step "Creating the first administrator '$($cfg.BOOTSTRAP_ADMIN_USERNAME)'"
    Invoke-Compose -Arguments @('run', '--rm', '--no-deps', '--user', 'root', '-T',
        '-v', "$(Join-Path $script:Root 'tools'):/tools:ro",
        '-e', "BOOTSTRAP_ADMIN_USERNAME=$($cfg.BOOTSTRAP_ADMIN_USERNAME)",
        '-e', "BOOTSTRAP_ADMIN_EMAIL=$($cfg.BOOTSTRAP_ADMIN_EMAIL)",
        '-e', "BOOTSTRAP_ADMIN_PASSWORD=$($cfg.BOOTSTRAP_ADMIN_PASSWORD)",
        '-e', "WIMS_HOST=$($cfg.WIMS_HOST)",
        '-e', 'KEYCLOAK_URL=http://keycloak:8080/auth',
        '--entrypoint', 'python', 'backend', '/tools/bootstrap_admin.py')
    # The temporary password is single-use; do not leave it in .env.
    Set-DotEnvValue 'BOOTSTRAP_ADMIN_PASSWORD' ''
    Write-Host '  The initial password was removed from .env.'
} else {
    Write-Host 'No pending administrator in .env: skipping (normal for an update).'
}

# 8. Firewall (optional) ----------------------------------------------------------------------------------------
if ($OpenFirewall) {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        if (-not (Get-NetFirewallRule -DisplayName 'WIMS-BFP HTTPS' -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -DisplayName 'WIMS-BFP HTTPS' -Direction Inbound -Protocol TCP -LocalPort 443, 80 -Action Allow -Profile Private,Domain | Out-Null
            Write-Host '  Firewall rule added (ports 443 and 80, Private/Domain networks).'
        }
    } else { Write-Host '  -OpenFirewall needs an administrator PowerShell; see INSTALL.md section 7.' -ForegroundColor Yellow }
}

Write-Host ''
Write-Host "WIMS-BFP is running: https://$($cfg.WIMS_HOST)" -ForegroundColor Green
Write-Host "Office PCs need the CA certificate once: certs\WIMS-BFP-CA.crt (INSTALL.md section 8)."
Write-Host 'First login forces a password change and one-time-code (OTP) enrolment.'
