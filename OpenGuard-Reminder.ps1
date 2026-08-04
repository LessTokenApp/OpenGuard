# OpenGuard Reminder - 15 dk kontrol
$ConfigFile = Join-Path $env:APPDATA "OpenGuard\config.txt"

function Load-ReminderConfig {
    $enabled = "Yes"
    if (Test-Path $ConfigFile) {
        Get-Content $ConfigFile -Encoding UTF8 | ForEach-Object {
            if ($_ -match "^\s*ReminderEnabled=(.*)$") { $enabled = $matches[1].Trim() }
        }
    }
    return $enabled
}

function Test-IsPublic {
    $profiles = Get-NetConnectionProfile -ErrorAction SilentlyContinue
    foreach ($p in $profiles) {
        if ($p.NetworkCategory -eq "Public") { return $true }
    }
    return $false
}

function Test-HardeningOn {
    $llmnr = Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Name "EnableMulticast" -ErrorAction SilentlyContinue
    if ($llmnr -and $llmnr.EnableMulticast -eq 0) { return $true }
    return $false
}

# Ana mantik
if ((Load-ReminderConfig) -ne "Yes") { exit }

if (-not (Test-IsPublic)) { exit }

if (Test-HardeningOn) { exit }

# Uyari goster
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show(
    "OpenGuard su anda devrede degil.`n`nBilgisayariniz korsanlik girisimlerine karsi daha savunmasiz olabilir.`n`nPublic bir agdasiniz. OpenGuard'i acmanizi oneririz.",
    "OpenGuard Hatirlatma",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Warning
) | Out-Null