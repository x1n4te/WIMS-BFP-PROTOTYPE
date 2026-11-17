<#
.SYNOPSIS
  Restores a backup onto this PC: both databases, uploaded files, and (on a new PC) .env and
  the certificate authority.
.DESCRIPTION
  Fresh PC:  install the container runtime, copy the bundle, then
               .\restore.ps1 -BackupFolder E:\WIMS-Backups\wims-backup-<stamp> -SecretsFolder F:\WIMS-Secrets\wims-backup-<stamp>-secrets
             (it restores .env + certs, runs install.ps1 for the images, then loads the data)
  Same PC:   the same command; it asks before replacing existing data.
  The restored .env must keep the SAME WIMS_MASTER_KEY, otherwise encrypted data is unreadable.
  Office PCs keep trusting the site because the restored CA is the same one.
#>
param(
    [Parameter(Mandatory)][string]$BackupFolder,
    [string]$SecretsFolder
)

. "$PSScriptRoot\common.ps1"
Assert-Docker

foreach ($f in 'wims.dump', 'keycloak.dump', 'attachments.tar.gz', 'manifest.json') {
    if (-not (Test-Path -LiteralPath (Join-Path $BackupFolder $f))) { Fail "Backup folder is missing $f" }
}

# Confirmation FIRST: nothing below changes anything until the operator types the database
# name (wims) or RESTORE exactly. There is deliberately no -Yes switch.
Write-Host ''
Write-Host 'This REPLACES all current WIMS data on this PC (the wims and keycloak databases and the uploaded files) with the backup.' -ForegroundColor Yellow
Write-Host "Backup: $BackupFolder"
$answer = Read-Host 'To continue type the database name (wims) or RESTORE'
if ($answer -cne 'wims' -and $answer -cne 'RESTORE') { Fail 'Not confirmed. Nothing was changed.' }

Write-Step 'Checking backup integrity'
$manifest = Get-Content -LiteralPath (Join-Path $BackupFolder 'manifest.json') -Raw | ConvertFrom-Json
foreach ($f in 'wims.dump', 'keycloak.dump', 'attachments.tar.gz') {
    $want = $manifest.files.$f.sha256
    if ((Get-FileSha256 (Join-Path $BackupFolder $f)) -ne $want) { Fail "$f does not match its checksum: the backup is damaged." }
    Write-Host "  ok  $f"
}

# Secrets ------------------------------------------------------------------------------------------
if ($SecretsFolder) {
    $savedEnv = Join-Path $SecretsFolder '.env'
    if (-not (Test-Path -LiteralPath $savedEnv)) { Fail "No .env in $SecretsFolder" }
    if (Test-Path -LiteralPath $script:EnvFile) {
        $cur = Read-DotEnv; $old = Read-DotEnv $savedEnv
        if ($cur.WIMS_MASTER_KEY -ne $old.WIMS_MASTER_KEY) {
            Fail 'The current .env has a DIFFERENT master key than the backup. Restoring would leave encrypted data unreadable. Move the current .env away and run again to use the backup''s .env.'
        }
    } else {
        Write-Step 'Restoring .env and certificates from the secrets backup'
        Copy-Item -LiteralPath $savedEnv -Destination $script:EnvFile
        $savedCerts = Join-Path $SecretsFolder 'certs'
        if (Test-Path -LiteralPath $savedCerts) { Copy-Item -LiteralPath $savedCerts -Destination (Join-Path $script:Root 'certs') -Recurse -Force }
    }
}
if (-not (Test-Path -LiteralPath $script:EnvFile)) { Fail 'No .env on this PC. Pass -SecretsFolder with the backed-up secrets folder.' }
$cfg = Read-DotEnv

# Stack: make sure the images are loaded and postgres is up ------------------------------------
if (-not (Test-ImageLoaded $script:BackendImage)) { Write-Step 'Images not loaded: running install.ps1 first'; & "$PSScriptRoot\install.ps1" -SkipBackup }
Invoke-Compose -Arguments @('up', '-d', 'postgres')
Wait-ContainersReady -Names @('wims-postgres')

Write-Step 'Stopping the application services'
Invoke-Compose -Arguments @('stop', 'nginx', 'frontend', 'backend', 'celery-worker', 'keycloak')

$base = @('run', '--rm', '--user', 'root', '--network', $script:ComposeNetwork, '-e', "PGPASSWORD=$($cfg.POSTGRES_PASSWORD)", '-v', "${BackupFolder}:/backup:ro", '--entrypoint')
function Invoke-Psql([string]$Sql) {
    Invoke-Native -Exe 'docker' -Arguments ($base + @('psql', $script:BackendImage, '-h', 'postgres', '-U', 'postgres', '-d', 'postgres', '-v', 'ON_ERROR_STOP=1', '-c', $Sql))
}

Write-Step 'Recreating the databases'
Invoke-Psql 'DROP DATABASE IF EXISTS wims WITH (FORCE)'
Invoke-Psql 'DROP DATABASE IF EXISTS keycloak WITH (FORCE)'
Invoke-Psql 'CREATE DATABASE wims TEMPLATE template0'
Invoke-Psql 'CREATE DATABASE keycloak OWNER keycloak TEMPLATE template0'

foreach ($pair in @(@('wims', 'wims.dump'), @('keycloak', 'keycloak.dump'))) {
    Write-Step "Restoring database $($pair[0])"
    $r = Invoke-Quiet -Exe 'docker' -Arguments ($base + @('pg_restore', $script:BackendImage, '-h', 'postgres', '-U', 'postgres', '-d', $pair[0], '--no-owner', '--role=postgres', "/backup/$($pair[1])"))
    if ($r.ExitCode -ne 0) {
        Write-Host "pg_restore reported problems for $($pair[0]) (last lines):" -ForegroundColor Yellow
        $r.Output | Select-Object -Last 15 | ForEach-Object { Write-Host "  $_" }
        Write-Host 'Warnings such as "already exists" are usually harmless; any other error must be checked before using the system.' -ForegroundColor Yellow
    }
}
# --no-owner makes the postgres role own the keycloak tables; hand them back to the keycloak role.
Invoke-Native -Exe 'docker' -Arguments ($base + @('psql', $script:BackendImage, '-h', 'postgres', '-U', 'postgres', '-d', 'keycloak', '-v', 'ON_ERROR_STOP=1', '-c',
    "DO `$`$ DECLARE r record; BEGIN FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='public' LOOP EXECUTE format('ALTER TABLE public.%I OWNER TO keycloak', r.tablename); END LOOP; FOR r IN SELECT sequencename FROM pg_sequences WHERE schemaname='public' LOOP EXECUTE format('ALTER SEQUENCE public.%I OWNER TO keycloak', r.sequencename); END LOOP; END `$`$;"))

Write-Step 'Restoring uploaded files'
Invoke-Native -Exe 'docker' -Arguments @('run', '--rm', '--user', 'root', '-v', 'wims_attachments:/data', '-v', "${BackupFolder}:/backup:ro",
    '--entrypoint', 'sh', $script:BackendImage, '-c', 'find /data -mindepth 1 -delete && tar xzf /backup/attachments.tar.gz -C /data')

Write-Step 'Starting everything'
Invoke-Compose -Arguments @('up', '-d', '--pull', 'never')
Wait-ContainersReady -Names @('wims-postgres', 'wims-redis', 'wims-keycloak', 'wims-backend', 'wims-celery-worker', 'wims-frontend', 'wims-nginx')

Write-Host ''
Write-Host "Restore complete. Sign in at https://$($cfg.WIMS_HOST) with an account that existed at backup time." -ForegroundColor Green
Write-Host 'Check: incident counts, a user login with OTP, and an encrypted field (DEPLOYMENT_TEST_CHECKLIST.md, section 12).'
