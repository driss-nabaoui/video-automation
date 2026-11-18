<#
.SYNOPSIS
    VOIDORA — Local Windows 11 <-> VPS Media Synchronization & Job Dispatcher
.DESCRIPTION
    Automates uploading raw assets from Windows to the Contabo VPS, triggering
    the VOIDORA AI video processing pipeline, and downloading rendered videos.
.EXAMPLE
    .\sync_from_windows.ps1 -Action Push -LocalPath "C:\VoidoraMedia\Inbox"
    .\sync_from_windows.ps1 -Action Pull -LocalPath "C:\VoidoraMedia\Output"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("Push", "Pull", "Status")]
    [string]$Action = "Push",

    [Parameter(Mandatory=$false)]
    [string]$VpsHost = "157.173.117.150",

    [Parameter(Mandatory=$false)]
    [string]$VpsUser = "root",

    [Parameter(Mandatory=$false)]
    [string]$RemoteInbox = "/opt/video-automation/media/01_raw_inbox",

    [Parameter(Mandatory=$false)]
    [string]$RemoteOutput = "/opt/video-automation/media/06_rendered_output",

    [Parameter(Mandatory=$false)]
    [string]$LocalPath = "$HOME\VoidoraMedia"
)

# Ensure local directories exist
$LocalInbox = Join-Path $LocalPath "Inbox"
$LocalRendered = Join-Path $LocalPath "Output"

if (!(Test-Path -Path $LocalInbox)) { New-Item -ItemType Directory -Path $LocalInbox -Force | Out-Null }
if (!(Test-Path -Path $LocalRendered)) { New-Item -ItemType Directory -Path $LocalRendered -Force | Out-Null }

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  VOIDORA — Local Media Bridge (Windows 11 <-> VPS)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

switch ($Action) {
    "Push" {
        Write-Host "[+] Scanning local inbox: $LocalInbox" -ForegroundColor Yellow
        $files = Get-ChildItem -Path $LocalInbox -File
        if ($files.Count -eq 0) {
            Write-Host "[-] No media files found in $LocalInbox." -ForegroundColor Red
            Write-Host "    Place video clips, images, or audio files there and rerun this script." -ForegroundColor Gray
            return
        }

        Write-Host "[+] Found $($files.Count) file(s). Uploading to VPS ($RemoteInbox)..." -ForegroundColor Green
        scp -r "$LocalInbox/*" "$($VpsUser)@$($VpsHost):$($RemoteInbox)/"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✔] Upload complete. Assets safely staged in VPS inbox." -ForegroundColor Green
        } else {
            Write-Host "[✖] Upload encountered an error. Check SSH connection." -ForegroundColor Red
        }
    }

    "Pull" {
        Write-Host "[+] Downloading rendered videos from VPS ($RemoteOutput) to $LocalRendered..." -ForegroundColor Yellow
        scp "$($VpsUser)@$($VpsHost):$($RemoteOutput)/*.mp4" "$LocalRendered/"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✔] Download complete. Rendered videos available in $LocalRendered." -ForegroundColor Green
        } else {
            Write-Host "[!] Note: Ensure videos exist on VPS. (Exit code: $LASTEXITCODE)" -ForegroundColor Gray
        }
    }

    "Status" {
        Write-Host "[+] Checking VPS video worker health..." -ForegroundColor Yellow
        ssh "$($VpsUser)@$($VpsHost)" "docker exec automation-video-worker curl -s http://localhost:8000/health"
    }
}
