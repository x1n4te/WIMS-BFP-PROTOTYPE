<#
.SYNOPSIS
  Run on each OFFICE PC (not the server) to trust the WIMS-BFP certificate authority.
  Right-click this file > "Run with PowerShell" from an administrator account, with
  WIMS-BFP-CA.crt in the same folder.
#>
$ErrorActionPreference = 'Stop'
$ca = Join-Path $PSScriptRoot 'WIMS-BFP-CA.crt'
if (-not (Test-Path -LiteralPath $ca)) { throw "WIMS-BFP-CA.crt not found next to this script." }
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this as Administrator (right-click PowerShell > Run as administrator).'
}
Import-Certificate -FilePath $ca -CertStoreLocation Cert:\LocalMachine\Root | Out-Null
Write-Host 'WIMS-BFP certificate authority installed. Close and reopen Edge/Chrome.' -ForegroundColor Green
Write-Host 'Firefox keeps its own list: Settings > Privacy & Security > Certificates > View Certificates > Authorities > Import.'
