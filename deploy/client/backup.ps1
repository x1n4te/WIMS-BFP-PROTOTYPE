<#
.SYNOPSIS
  Backs up everything needed to rebuild WIMS-BFP: both databases, uploaded files, and (in a
  separate folder) .env with the master encryption key and the certificate authority.
.DESCRIPTION
  Output, for -Destination D:\WIMS-Backups:
    D:\WIMS-Backups\wims-backup-<date-time>\          database + files (encrypted PII stays encrypted)
        wims.dump  keycloak.dump  attachments.tar.gz  manifest.json
    D:\WIMS-Backups\wims-backup-<date-time>-secrets\  .env (MASTER KEY, passwords) + certs\
  KEEP THE -secrets FOLDER SEPARATE from the data folder (different USB stick or a safe).
  Data without the master key is unreadable; the key next to the data defeats the encryption if
  the media is lost. Use -SecretsDestination to write the secrets elsewhere in one run.
.EXAMPLE
  .\backup.ps1 -Destination E:\WIMS-Backups -SecretsDestination F:\WIMS-Secrets
#>
param(
    [Parameter(Mandatory)][string]$Destination,
    [string]$SecretsDestination,
    [int]$KeepLast = 14
)

. "$PSScriptRoot\common.ps1"
Assert-Docker
$cfg = Read-DotEnv
if (-not $cfg.ContainsKey('POSTGRES_PASSWORD')) { Fail '.env not found or incomplete.' }
foreach ($c in 'wims-postgres') { if ((Get-ContainerHealth $c) -ne 'healthy') { Fail "$c is not running/healthy. Start the stack first (install.ps1 or docker compose up -d)." } }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dataDir = Join-Path $Destination "wims-backup-$stamp"
if (-not $SecretsDestination) { $SecretsDestination = $Destination }
$secretsDir = Join-Path $SecretsDestination "wims-backup-$stamp-secrets"
New-Item -ItemType Directory -Force -Path $dataDir, $secretsDir | Out-Null

$pg = @('run', '--rm', '--user', 'root', '--network', $script:ComposeNetwork, '-e', "PGPASSWORD=$($cfg.POSTGRES_PASSWORD)", '-v', "${dataDir}:/backup", '--entrypoint')

Write-Step 'Dumping the WIMS database'
Invoke-Native -Exe 'docker' -Arguments ($pg + @('pg_dump', $script:BackendImage, '-h', 'postgres', '-U', 'postgres', '-Fc', '-f', '/backup/wims.dump', 'wims'))
Write-Step 'Dumping the login (Keycloak) database'
Invoke-Native -Exe 'docker' -Arguments ($pg + @('pg_dump', $script:BackendImage, '-h', 'postgres', '-U', 'postgres', '-Fc', '-f', '/backup/keycloak.dump', 'keycloak'))

Write-Step 'Archiving uploaded files'
Invoke-Native -Exe 'docker' -Arguments @('run', '--rm', '--user', 'root', '-v', 'wims_attachments:/data:ro', '-v', "${dataDir}:/backup",
    '--entrypoint', 'tar', $script:BackendImage, 'czf', '/backup/attachments.tar.gz', '-C', '/data', '.')

Write-Step 'Verifying the dumps are readable'
foreach ($f in 'wims.dump', 'keycloak.dump') {
    $r = Invoke-Quiet -Exe 'docker' -Arguments @('run', '--rm', '--user', 'root', '-v', "${dataDir}:/backup:ro", '--entrypoint', 'pg_restore', $script:BackendImage, '-l', "/backup/$f")
    if ($r.ExitCode -ne 0 -or $r.Output.Count -lt 20) { Fail "$f failed verification. This backup is NOT usable; do not rely on it." }
}
$r = Invoke-Quiet -Exe 'docker' -Arguments @('run', '--rm', '--user', 'root', '-v', "${dataDir}:/backup:ro", '--entrypoint', 'tar', $script:BackendImage, 'tzf', '/backup/attachments.tar.gz')
if ($r.ExitCode -ne 0) { Fail 'attachments.tar.gz failed verification. This backup is NOT usable.' }

Write-Step 'Saving secrets (master key, passwords, certificates)'
Copy-Item -LiteralPath $script:EnvFile -Destination (Join-Path $secretsDir '.env')
$certDir = Join-Path $script:Root 'certs'
if (Test-Path -LiteralPath $certDir) { Copy-Item -LiteralPath $certDir -Destination (Join-Path $secretsDir 'certs') -Recurse -Force }

$manifest = [ordered]@{
    created   = (Get-Date).ToString('s')
    host      = $cfg.WIMS_HOST
    files     = [ordered]@{}
    secrets   = (Split-Path -Leaf $secretsDir)
}
foreach ($f in 'wims.dump', 'keycloak.dump', 'attachments.tar.gz') {
    $p = Join-Path $dataDir $f
    $manifest.files[$f] = [ordered]@{ bytes = (Get-Item -LiteralPath $p).Length; sha256 = (Get-FileSha256 $p) }
}
[System.IO.File]::WriteAllText((Join-Path $dataDir 'manifest.json'), ($manifest | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding($false)))

# Retention (data folders only; secrets folders are never deleted automatically).
$old = Get-ChildItem -LiteralPath $Destination -Directory -Filter 'wims-backup-*' | Where-Object { $_.Name -notlike '*-secrets' } | Sort-Object Name -Descending | Select-Object -Skip $KeepLast
foreach ($d in $old) { Remove-Item -LiteralPath $d.FullName -Recurse -Force; Write-Host "  removed old backup $($d.Name)" }

Write-Host ''
Write-Host "Backup complete:" -ForegroundColor Green
Write-Host "  data:    $dataDir"
Write-Host "  secrets: $secretsDir   <-- store separately and safely (contains the master key)" -ForegroundColor Yellow
Write-Host 'Now copy BOTH folders to external media.'
