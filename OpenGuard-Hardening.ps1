#requires -RunAsAdministrator
#requires -Version 5.1

<#
.SYNOPSIS
    OpenGuard Hardening – VPN’siz halka açık ağ sertleştirme

.DESCRIPTION
    VPN kullanmadan halka açık Wi-Fi ağlarında saldırı yüzeyini küçültür.
    Trafiği şifrelemez. Dinleme ve MITM riskini ortadan kaldırmaz.
    Sadece keşif, paylaşım ve gereksiz servisleri kapatarak riski azaltır.

.NOTES
    Proje  : OpenGuard
    Sürüm  : 0.1.1
    Tarih  : 2026-07-31
#>

[CmdletBinding(DefaultParameterSetName = "Status")]
param (
    [Parameter(ParameterSetName = "Enable")]
    [switch]$Enable,

    [Parameter(ParameterSetName = "Disable")]
    [switch]$Disable,

    [Parameter(ParameterSetName = "Status")]
    [switch]$Status,

    [Parameter(ParameterSetName = "Enable")]
    [switch]$Aggressive
)

$RulePrefix = "OpenGuard-Hardening"
$Version    = "0.1.1"

function Write-OG {
    param(
        [string]$Message,
        [ValidateSet("INFO","SUCCESS","WARN","ERROR")]
        [string]$Level = "INFO"
    )
    $ts = Get-Date -Format "HH:mm:ss"
    $color = @{
        "INFO"    = "Cyan"
        "SUCCESS" = "Green"
        "WARN"    = "Yellow"
        "ERROR"   = "Red"
    }[$Level]
    Write-Host "[$ts] " -NoNewline -ForegroundColor DarkGray
    Write-Host ("[{0,-7}] " -f $Level) -NoNewline -ForegroundColor $color
    Write-Host $Message
}

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-CurrentNetworkProfiles {
    Get-NetConnectionProfile | Select-Object Name, InterfaceAlias, NetworkCategory, IPv4Connectivity
}

function Set-NetworkToPublic {
    $profiles = Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -ne "DomainAuthenticated" }
    if (-not $profiles) {
        Write-OG "Değiştirilecek ağ profili bulunamadı." "WARN"
        return
    }
    foreach ($p in $profiles) {
        try {
            Set-NetConnectionProfile -InterfaceIndex $p.InterfaceIndex -NetworkCategory Public -ErrorAction Stop
            Write-OG "Ağ profili Public yapıldı → $($p.Name) ($($p.InterfaceAlias))" "SUCCESS"
        }
        catch {
            Write-OG "Profil değiştirilemedi: $($p.Name) – $($_.Exception.Message)" "WARN"
        }
    }
}

function Disable-NetworkDiscoveryAndSharing {
    $groups = @(
        "Network Discovery",
        "File and Printer Sharing",
        "File and Printer Sharing over SMBDirect"
    )

    foreach ($g in $groups) {
        $rules = Get-NetFirewallRule -DisplayGroup $g -ErrorAction SilentlyContinue
        if ($rules) {
            $rules | Set-NetFirewallRule -Enabled False -ErrorAction SilentlyContinue
            Write-OG "Firewall grubu kapatıldı: $g" "INFO"
        }
        else {
            Write-OG "Firewall grubu bulunamadı (dil farkı olabilir): $g" "WARN"
        }
    }

    $servicesToStop = @("FDResPub", "SSDPSRV", "upnphost")
    foreach ($svcName in $servicesToStop) {
        $s = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($s) {
            try {
                if ($s.Status -eq "Running") {
                    Stop-Service -Name $svcName -Force -ErrorAction Stop
                    Write-OG "Servis durduruldu: $svcName" "INFO"
                }
                Set-Service -Name $svcName -StartupType Manual -ErrorAction SilentlyContinue
            }
            catch {
                Write-OG "Servis işlenemedi: $svcName – $($_.Exception.Message)" "WARN"
            }
        }
    }
}

function Disable-LLMNR {
    $regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"
    if (-not (Test-Path $regPath)) {
        New-Item -Path $regPath -Force | Out-Null
    }
    Set-ItemProperty -Path $regPath -Name "EnableMulticast" -Value 0 -Type DWord -Force
    Write-OG "LLMNR kapatıldı (EnableMulticast = 0)" "INFO"
}

function Disable-NetBIOS {
    $adapters = Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" -ErrorAction SilentlyContinue
    if (-not $adapters) {
        $adapters = Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled }
    }

    foreach ($a in $adapters) {
        try {
            $a.SetTcpipNetbios(2) | Out-Null
            Write-OG "NetBIOS kapatıldı → $($a.Description)" "INFO"
        }
        catch {
            Write-OG "NetBIOS kapatılamadı: $($a.Description)" "WARN"
        }
    }
}

function Set-FirewallPublicTight {
    $extraGroups = @(
        "Windows Media Player Network Sharing Service",
        "AllJoyn Router",
        "Cast to Device functionality",
        "Remote Desktop",
        "Remote Assistance",
        "Windows Remote Management"
    )

    foreach ($g in $extraGroups) {
        $rules = Get-NetFirewallRule -DisplayGroup $g -ErrorAction SilentlyContinue
        if ($rules) {
            $rules | Where-Object { $_.Profile -match "Public|Any" } |
                Set-NetFirewallRule -Enabled False -ErrorAction SilentlyContinue
            Write-OG "Public profilde kapatıldı: $g" "INFO"
        }
    }
}

function Enable-AggressiveMode {
    Write-OG "Agresif mod isteniyor..." "WARN"
    Write-OG "Bu mod sadece TCP 80/443 ve DNS (53) çıkışına izin verir." "WARN"
    Write-OG "Windows Update, bazı uygulamalar ve diğer servisler bozulabilir." "WARN"
    Write-Host ""

    Get-NetFirewallRule -DisplayName "$RulePrefix-Agg*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule

    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Allow DNS UDP" `
        -Direction Outbound -Action Allow -Protocol UDP -RemotePort 53 `
        -Profile Public -Enabled True | Out-Null

    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Allow DNS TCP" `
        -Direction Outbound -Action Allow -Protocol TCP -RemotePort 53 `
        -Profile Public -Enabled True | Out-Null

    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Allow HTTP" `
        -Direction Outbound -Action Allow -Protocol TCP -RemotePort 80 `
        -Profile Public -Enabled True | Out-Null

    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Allow HTTPS" `
        -Direction Outbound -Action Allow -Protocol TCP -RemotePort 443 `
        -Profile Public -Enabled True | Out-Null

    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Block All Other" `
        -Direction Outbound -Action Block -Profile Public -Enabled True | Out-Null

    Write-OG "Agresif kurallar eklendi." "SUCCESS"
}

function Remove-AggressiveRules {
    $rules = Get-NetFirewallRule -DisplayName "$RulePrefix-Agg*" -ErrorAction SilentlyContinue
    if ($rules) {
        $rules | Remove-NetFirewallRule
        Write-OG "Agresif kurallar kaldırıldı." "INFO"
    }
}

function Restore-Defaults {
    Write-OG "Sertleştirmeler geri alınıyor..." "INFO"

    $regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"
    if (Test-Path $regPath) {
        Remove-ItemProperty -Path $regPath -Name "EnableMulticast" -ErrorAction SilentlyContinue
        Write-OG "LLMNR policy kaldırıldı" "INFO"
    }

    $adapters = Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" -ErrorAction SilentlyContinue
    if (-not $adapters) {
        $adapters = Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled }
    }
    foreach ($a in $adapters) {
        try { $a.SetTcpipNetbios(0) | Out-Null } catch {}
    }
    Write-OG "NetBIOS ayarları varsayılana döndürüldü" "INFO"

    foreach ($svcName in @("FDResPub", "SSDPSRV", "upnphost")) {
        $s = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($s) {
            Set-Service -Name $svcName -StartupType Manual -ErrorAction SilentlyContinue
        }
    }

    foreach ($g in @("Network Discovery", "File and Printer Sharing")) {
        Get-NetFirewallRule -DisplayGroup $g -ErrorAction SilentlyContinue |
            Set-NetFirewallRule -Enabled True -ErrorAction SilentlyContinue
    }

    Remove-AggressiveRules
    Write-OG "Sertleştirmeler geri alındı." "SUCCESS"
    Write-OG "Not: Ağ profili otomatik geri alınmaz. İsterseniz elle Private yapabilirsiniz." "INFO"
}

function Enable-Hardening {
    Write-OG "OpenGuard Hardening başlatılıyor (VPN’siz)..." "INFO"
    Write-Host ""
    Write-OG "UYARI: Bu araç trafiği şifrelemez. Dinleme / MITM riskini ortadan kaldırmaz." "WARN"
    Write-OG "Sadece saldırı yüzeyini (keşif, paylaşım, eski protokoller) küçültür." "WARN"
    Write-Host ""

    Set-NetworkToPublic
    Disable-NetworkDiscoveryAndSharing
    Disable-LLMNR
    Disable-NetBIOS
    Set-FirewallPublicTight

    if ($Aggressive) {
        Write-Host ""
        Enable-AggressiveMode
    }

    Write-Host ""
    Write-OG "Hardening tamamlandı." "SUCCESS"
    Write-OG "Kapatmak için: .\OpenGuard-Hardening.ps1 -Disable" "INFO"
}

function Show-Status {
    Write-Host ""
    Write-Host "  OpenGuard Hardening  v$Version" -ForegroundColor White
    Write-Host "  ────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "  Mevcut ağ profilleri:" -ForegroundColor Cyan
    Get-CurrentNetworkProfiles | Format-Table -AutoSize

    $llmnr = Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Name "EnableMulticast" -ErrorAction SilentlyContinue
    if ($llmnr -and $llmnr.EnableMulticast -eq 0) {
        Write-Host "  LLMNR          : KAPALI" -ForegroundColor Green
    } else {
        Write-Host "  LLMNR          : Açık / Varsayılan" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "  İlgili servisler:" -ForegroundColor Cyan
    foreach ($svcName in @("FDResPub", "SSDPSRV", "upnphost")) {
        $s = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($s) {
            $statusColor = if ($s.Status -eq "Running") { "Yellow" } else { "Green" }
            Write-Host ("  {0,-12} : {1,-10} ({2})" -f $svcName, $s.Status, $s.StartType) -ForegroundColor $statusColor
        }
    }

    $agg = Get-NetFirewallRule -DisplayName "$RulePrefix-Agg*" -ErrorAction SilentlyContinue
    Write-Host ""
    if ($agg) {
        Write-Host "  Agresif mod    : AKTİF ($($agg.Count) kural)" -ForegroundColor Yellow
    } else {
        Write-Host "  Agresif mod    : Kapalı" -ForegroundColor DarkGray
    }

    Write-Host ""
    Write-Host "  Not: Bu mod VPN yerine geçmez. Sadece yüzey küçültür." -ForegroundColor DarkGray
    Write-Host ""
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════╗" -ForegroundColor DarkCyan
Write-Host "  ║     OpenGuard Hardening (VPN’siz)    ║" -ForegroundColor White
Write-Host "  ║           v$Version                     ║" -ForegroundColor DarkGray
Write-Host "  ╚══════════════════════════════════════╝" -ForegroundColor DarkCyan
Write-Host ""

if (-not (Test-IsAdmin)) {
    Write-OG "Bu script Yönetici olarak çalıştırılmalıdır!" "ERROR"
    exit 1
}

switch ($PSCmdlet.ParameterSetName) {
    "Enable"  { Enable-Hardening }
    "Disable" { Restore-Defaults }
    default   { Show-Status }
}