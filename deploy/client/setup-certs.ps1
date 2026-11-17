<#
.SYNOPSIS
  Creates the local certificate authority (once) and a server certificate for the WIMS hostname
  plus the server's static IP. Prints where the CA certificate for the office PCs is.
.DESCRIPTION
  install.ps1 runs this automatically when no certificate exists. Run it again by hand after the
  server's IP changes: the CA is reused, so office PCs do NOT need the CA installed again.
  Needs the wims-backend:client image (loaded by install.ps1); it runs Python's `cryptography`
  inside that container, so no openssl or Python is needed on Windows.
#>
param()

. "$PSScriptRoot\common.ps1"
Assert-Docker

$cfg = Read-DotEnv
if (-not $cfg.ContainsKey('WIMS_HOST') -or -not $cfg.ContainsKey('WIMS_SERVER_IP')) {
    Fail '.env is missing WIMS_HOST / WIMS_SERVER_IP. Run setup-secrets.ps1 first.'
}
if (-not (Test-ImageLoaded $script:BackendImage)) { Fail "Image $script:BackendImage is not loaded yet. Run install.ps1 (it loads the bundle first)." }

Write-Step "Issuing certificate for $($cfg.WIMS_HOST) and $($cfg.WIMS_SERVER_IP)"
$certs = Join-Path $script:Root 'certs'
New-Item -ItemType Directory -Force -Path $certs | Out-Null
Invoke-Tool -Script 'gen_certs.py' -ScriptArgs @('/out', $cfg.WIMS_HOST, $cfg.WIMS_SERVER_IP) -Mounts @('-v', "${certs}:/out")

$caSrc = Join-Path $certs 'ca\ca.crt'
$caOut = Join-Path $certs 'WIMS-BFP-CA.crt'
Copy-Item -LiteralPath $caSrc -Destination $caOut -Force
Copy-Item -LiteralPath (Join-Path $script:Root 'install-ca-office-pc.ps1') -Destination (Join-Path $certs 'install-ca-office-pc.ps1') -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host 'Done.' -ForegroundColor Green
Write-Host "Give this file to EVERY office PC:  $caOut" -ForegroundColor Yellow
Write-Host '(public certificate only; safe to copy on a USB stick). Install steps: INSTALL.md section 8.'
Write-Host "NEVER copy certs\ca\ca.key anywhere except your secrets backup."
Write-Host 'If nginx is already running, apply the new certificate with:  docker compose restart nginx'
