<#
.SYNOPSIS
  BUILD MACHINE ONLY (x86-64 Windows or Linux PC with Docker and internet).
  Builds every image for linux/amd64 with the client settings baked in, assembles the clean
  database init files, and writes the install bundle: one `docker save` archive + SHA-256 sums.
.DESCRIPTION
  The client PC is x86. Build the release bundle on an x86 machine: cross-building the Next.js
  frontend under emulation (for example on an Apple Silicon Mac) works but is very slow.
  The frontend bakes WimsHost into its JavaScript, so a different hostname needs a new bundle.
.EXAMPLE
  .\build-bundle.ps1 -OutDir D:\wims-bundle
#>
param(
    [string]$WimsHost = 'wims.bfp.lan',
    [Parameter(Mandatory)][string]$OutDir,
    [switch]$SkipBuild
)

. "$PSScriptRoot\common.ps1"
Assert-Docker

$OutDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutDir)
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$initSrc = Join-Path $repo 'src\postgres-init'
$initDst = Join-Path $PSScriptRoot 'postgres-init'

# 1. Assemble the client database init files (explicit include list) ------------------------------
Write-Step 'Assembling clean-data postgres-init from init-files.txt'
if (Test-Path -LiteralPath $initDst) { Remove-Item -LiteralPath $initDst -Recurse -Force }
New-Item -ItemType Directory -Force -Path $initDst | Out-Null
$listed = [System.IO.File]::ReadAllLines((Join-Path $PSScriptRoot 'init-files.txt')) | Where-Object { $_.Trim() -ne '' -and -not $_.TrimStart().StartsWith('#') } | ForEach-Object { $_.Trim() }
$onDisk = Get-ChildItem -LiteralPath $initSrc -Filter '*.sql' | ForEach-Object { $_.Name }
$forbidden = @('03a_dev_users.sql', '14a_assign_ncr_to_test_users.sql', '14b_assign_ncr_to_team_accounts.sql', '29_seed_incidents.sql', '38_seed_security_threat_logs.sql')
foreach ($f in $listed) {
    if ($forbidden -contains $f) { Fail "init-files.txt lists dev/demo file $f" }
    if ($onDisk -notcontains $f) { Fail "init-files.txt lists $f but it is not in src\postgres-init" }
    Copy-Item -LiteralPath (Join-Path $initSrc $f) -Destination (Join-Path $initDst $f)
}
$unlisted = $onDisk | Where-Object { ($listed -notcontains $_) -and ($forbidden -notcontains $_) }
if ($unlisted) { Fail "New postgres-init file(s) not classified in init-files.txt: $($unlisted -join ', '). Add each to the include list or to the exclusions." }
Copy-Item -Path (Join-Path $PSScriptRoot 'init-extra\*') -Destination $initDst
Write-Host "  $($listed.Count) SQL files + client scripts"

# 2. Build images ------------------------------------------------------------------------------------
$env:WIMS_HOST = $WimsHost
if (-not $SkipBuild) {
    Write-Step "Building linux/amd64 images for https://$WimsHost (this takes a while)"
    # Build-only placeholders so compose can interpolate; nothing secret is baked into images.
    foreach ($n in 'POSTGRES_PASSWORD', 'KC_DB_PASSWORD', 'WIMS_APP_DB_PASSWORD', 'KEYCLOAK_ADMIN_PASSWORD', 'WIMS_MASTER_KEY') { Set-Item -Path "Env:$n" -Value 'build-only' }
    $env:DOCKER_DEFAULT_PLATFORM = 'linux/amd64'
    Invoke-Native -Exe 'docker' -Arguments @('compose', '--project-name', 'wims-build', '--project-directory', $PSScriptRoot,
        '-f', (Join-Path $PSScriptRoot 'docker-compose.yml'), '-f', (Join-Path $PSScriptRoot 'docker-compose.build.yml'), 'build', '--pull', 'backend', 'keycloak', 'frontend')
    foreach ($img in 'postgis/postgis:15-3.4-alpine', 'redis:8.8-alpine', 'nginx:1.30.3-alpine') {
        Invoke-Native -Exe 'docker' -Arguments @('pull', '--platform', 'linux/amd64', $img)
    }
}

# 3. Save the bundle ---------------------------------------------------------------------------------------
Write-Step "Writing bundle to $OutDir"
$images = @('wims-backend:client', 'wims-frontend:client', 'wims-keycloak:client', 'postgis/postgis:15-3.4-alpine', 'redis:8.8-alpine', 'nginx:1.30.3-alpine')
foreach ($img in $images) {
    $arch = (Invoke-Quiet -Exe 'docker' -Arguments @('image', 'inspect', '--format', '{{.Architecture}}', $img)).Output -join ''
    if ($arch.Trim() -ne 'amd64') { Fail "$img is '$arch', not amd64. Build on an x86-64 Docker host." }
}
New-Item -ItemType Directory -Force -Path (Join-Path $OutDir 'images'), (Join-Path $OutDir 'tools'), (Join-Path $OutDir 'keycloak') | Out-Null
Invoke-Native -Exe 'docker' -Arguments (@('save', '-o', (Join-Path $OutDir 'images\wims-images.tar')) + $images)

foreach ($f in 'docker-compose.yml', 'nginx.conf', 'common.ps1', 'setup-secrets.ps1', 'setup-certs.ps1', 'install.ps1', 'backup.ps1', 'restore.ps1', 'schedule-backup.ps1', 'install-ca-office-pc.ps1', 'INSTALL.md', 'DEPLOYMENT_TEST_CHECKLIST.md') {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $f) -Destination (Join-Path $OutDir $f) -Force
}
Copy-Item -Path (Join-Path $PSScriptRoot 'tools\*.py') -Destination (Join-Path $OutDir 'tools') -Force
Copy-Item -LiteralPath $initDst -Destination (Join-Path $OutDir 'postgres-init') -Recurse -Force
Copy-Item -LiteralPath (Join-Path $repo 'src\keycloak\import\bfp-realm.json') -Destination (Join-Path $OutDir 'keycloak\bfp-realm.json') -Force

$commit = (Invoke-Quiet -Exe 'git' -Arguments @('-C', $repo, 'rev-parse', '--short', 'HEAD')).Output -join ''
$version = [ordered]@{ built = (Get-Date).ToString('s'); host = $WimsHost; commit = $commit.Trim(); images = $images }
[System.IO.File]::WriteAllText((Join-Path $OutDir 'VERSION.json'), ($version | ConvertTo-Json), (New-Object System.Text.UTF8Encoding($false)))

Write-Step 'Computing SHA-256 checksums'
$lines = @()
foreach ($f in (Get-ChildItem -LiteralPath $OutDir -Recurse -File | Where-Object { $_.Name -ne 'SHA256SUMS.txt' })) {
    $rel = $f.FullName.Substring($OutDir.TrimEnd('\').Length + 1).Replace('\', '/')
    $lines += "$(Get-FileSha256 $f.FullName)  $rel"
}
[System.IO.File]::WriteAllLines((Join-Path $OutDir 'images\SHA256SUMS.txt'), $lines, (New-Object System.Text.UTF8Encoding($false)))

Write-Host ''
Write-Host "Bundle ready: $OutDir" -ForegroundColor Green
Write-Host 'Copy the whole folder to the client PC (for example C:\WIMS). Do not zip it with Windows "Send to": the image file exceeds its 2 GB limit.'
