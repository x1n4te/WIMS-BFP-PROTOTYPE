<#
.SYNOPSIS
  Registers a Windows scheduled task that runs backup.ps1 every day. The task runs as the
  current user, so that user must be logged in and the container runtime running at that time.
  (No task is needed to start WIMS itself: containers use restart: unless-stopped and return by
  themselves once Rancher Desktop starts; see INSTALL.md section 10.)
.EXAMPLE
  .\schedule-backup.ps1 -Destination C:\WIMS-Backups -SecretsDestination C:\WIMS-Secrets -Time 18:00
#>
param(
    [Parameter(Mandatory)][string]$Destination,
    [string]$SecretsDestination,
    [string]$Time = '18:00'
)
. "$PSScriptRoot\common.ps1"
$argList = "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\backup.ps1`" -Destination `"$Destination`""
if ($SecretsDestination) { $argList += " -SecretsDestination `"$SecretsDestination`"" }
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argList
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName 'WIMS-BFP Daily Backup' -Action $action -Trigger $trigger -Settings $settings -Description 'WIMS-BFP database and files backup' -Force | Out-Null
Write-Host "Scheduled: every day at $Time -> $Destination" -ForegroundColor Green
Write-Host 'This writes to the PC itself. Copy the backup folders to external media (INSTALL.md section 11).'
