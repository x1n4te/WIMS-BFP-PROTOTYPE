<#
.SYNOPSIS
  Generates .env: random passwords, a real WIMS_MASTER_KEY, and the first administrator's details.
.DESCRIPTION
  Run ONCE per install, before install.ps1. It refuses to overwrite an existing .env because that
  would replace the master encryption key and make encrypted data unreadable. Use -Force only on
  a brand-new install that holds no data.
.EXAMPLE
  .\setup-secrets.ps1 -ServerIp 192.168.1.50
#>
param(
    [string]$WimsHost = 'wims.bfp.lan',
    [string]$ServerIp,
    [switch]$Force
)

. "$PSScriptRoot\common.ps1"

if ((Test-Path -LiteralPath $script:EnvFile) -and -not $Force) {
    Fail '.env already exists. It holds the master encryption key, so it is not overwritten. (Brand-new install with no data? Re-run with -Force.)'
}

function Read-Required([string]$Prompt, [string]$Pattern, [string]$Hint) {
    while ($true) {
        $v = (Read-Host $Prompt).Trim()
        if ($v -match $Pattern) { return $v }
        Write-Host "  $Hint" -ForegroundColor Yellow
    }
}

function ConvertFrom-Secure([System.Security.SecureString]$Secure) {
    $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try { return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

Write-Step 'Server address'
if (-not $ServerIp) {
    $ServerIp = Read-Required 'Static IP address of THIS PC (for example 192.168.1.50)' '^(\d{1,3}\.){3}\d{1,3}$' 'Enter an IPv4 address such as 192.168.1.50.'
}
if ($WimsHost -notmatch '^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$') { Fail "Invalid host name: $WimsHost" }

Write-Step 'First administrator (the only account created at install; you add the others in WIMS)'
$adminUser = Read-Required 'Administrator username (letters, digits . _ - @)' '^[A-Za-z0-9._@-]{3,64}$' 'Use 3-64 letters, digits or . _ @ -'
$adminEmail = Read-Required 'Administrator email' "^[^@\s']+@[^@\s']+\.[^@\s']+$" 'Enter a valid email address.'
while ($true) {
    $p1 = ConvertFrom-Secure (Read-Host 'Initial password (temporary: changed at first login)' -AsSecureString)
    $p2 = ConvertFrom-Secure (Read-Host 'Repeat the password' -AsSecureString)
    if ($p1 -ne $p2) { Write-Host '  The passwords do not match.' -ForegroundColor Yellow; continue }
    $ok = ($p1.Length -ge 12) -and ($p1 -cmatch '[A-Z]') -and ($p1 -cmatch '[a-z]') -and ($p1 -match '\d') -and ($p1 -match '[^A-Za-z0-9]')
    if (-not $ok) { Write-Host '  Needs 12+ characters with an uppercase letter, a lowercase letter, a digit and a symbol.' -ForegroundColor Yellow; continue }
    if ($p1.Contains("'") -or $p1.Contains('"')) { Write-Host '  Please avoid the apostrophe and double-quote characters.' -ForegroundColor Yellow; continue }
    break
}

Write-Step 'Email (optional - press Enter to skip; WIMS works without it)'
$smtpHost = (Read-Host 'SMTP server host (blank = no email)').Trim()
$smtp = @{ SMTP_HOST = ''; SMTP_PORT = '587'; SMTP_FROM = ''; SMTP_USER = ''; SMTP_PASSWORD = ''; SMTP_STARTTLS = 'true'; SMTP_AUTH = 'true' }
if ($smtpHost) {
    $smtp.SMTP_HOST = $smtpHost
    $port = (Read-Host 'SMTP port [587]').Trim()
    if ($port) { $smtp.SMTP_PORT = $port }
    $smtp.SMTP_FROM = (Read-Host 'From address').Trim()
    $smtp.SMTP_USER = (Read-Host 'SMTP username (blank if none)').Trim()
    if ($smtp.SMTP_USER) {
        $smtp.SMTP_PASSWORD = ConvertFrom-Secure (Read-Host 'SMTP password' -AsSecureString)
        if ($smtp.SMTP_PASSWORD.Contains("'")) { Fail "SMTP password must not contain an apostrophe (')." }
    } else { $smtp.SMTP_AUTH = 'false' }
}

Write-Step 'Generating secrets'
$values = [ordered]@{
    WIMS_HOST                  = $WimsHost
    WIMS_SERVER_IP             = $ServerIp
    POSTGRES_PASSWORD          = New-RandomPassword 32
    KC_DB_PASSWORD             = New-RandomPassword 32
    WIMS_APP_DB_PASSWORD       = New-RandomPassword 32
    KEYCLOAK_ADMIN             = 'kcadmin'
    KEYCLOAK_ADMIN_PASSWORD    = (New-RandomPassword 24) + '-Aa1'
    WIMS_MASTER_KEY            = New-MasterKey
    WIMS_KEYCLOAK_EVENT_SECRET = New-RandomPassword 40
    BOOTSTRAP_ADMIN_USERNAME   = $adminUser
    BOOTSTRAP_ADMIN_EMAIL      = $adminEmail
    BOOTSTRAP_ADMIN_PASSWORD   = $p1
}
foreach ($k in $smtp.Keys) { $values[$k] = $smtp[$k] }
Write-DotEnv $values

# Keep other local users out of the secrets file (inherit-only, current user full control).
$null = Invoke-Quiet -Exe 'icacls' -Arguments @($script:EnvFile, '/inheritance:r', '/grant:r', "$($env:USERNAME):(F)")

Write-Host ''
Write-Host '.env created.' -ForegroundColor Green
Write-Host 'IMPORTANT: back up .env (it holds WIMS_MASTER_KEY) to a SECOND safe place now.' -ForegroundColor Yellow
Write-Host 'Without that key, encrypted incident data and backups cannot be read. See INSTALL.md section 11.'
Write-Host 'Next: .\install.ps1'
