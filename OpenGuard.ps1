#requires -Version 5.1
# OpenGuard v0.6.0 - Analytics Dashboard + Advanced Features

# Run with no arguments for the interactive menu, unchanged.
# Pass -Action to drive the same operations programmatically, which is how the
# GUI calls this script. In that mode nothing prompts and nothing is drawn: the
# exit code carries the result.
param(
    [ValidateSet("Enable", "Disable", "Status")]
    [string]$Action,

    [ValidateSet("Basic", "Moderate", "Relaxed")]
    [string]$Level = "Moderate"
)

$Version   = "0.6.0"

# ============================================
# FirewallManager - Inline (v0.5.0)
# ============================================
function Get-FirewallLevels {
    return @{
        Basic = @(
            @{ Name = "DNS UDP"; Port = 53; Protocol = "UDP" }
            @{ Name = "DNS TCP"; Port = 53; Protocol = "TCP" }
            @{ Name = "HTTP"; Port = 80; Protocol = "TCP" }
            @{ Name = "HTTPS"; Port = 443; Protocol = "TCP" }
        )
        Moderate = @(
            @{ Name = "NTP"; Port = 123; Protocol = "UDP" }
            @{ Name = "DHCP"; Port = 67; Protocol = "UDP" }
            @{ Name = "DHCP client"; Port = 68; Protocol = "UDP" }
            @{ Name = "IMAP"; Port = 993; Protocol = "TCP" }
            @{ Name = "SMTP"; Port = 587; Protocol = "TCP" }
            @{ Name = "SSH"; Port = 22; Protocol = "TCP" }
        )
        Extended = @(
            @{ Name = "HTTP Alt"; Port = 8080; Protocol = "TCP" }
            @{ Name = "OpenVPN"; Port = 1194; Protocol = "UDP" }
            @{ Name = "WireGuard"; Port = 51820; Protocol = "UDP" }
        )
    }
}

function Enable-AdaptiveRules {
    param([ValidateSet("Basic", "Moderate", "Relaxed")][string]$Level = "Moderate")

    Write-Host ""
    Write-Host "  ========================================" -ForegroundColor Cyan
    Write-Host "  Adaptive Firewall: $Level modu" -ForegroundColor White
    Write-Host "  ========================================" -ForegroundColor Cyan
    Write-Host ""

    Get-NetFirewallRule -DisplayName "OpenGuard-Adaptive*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue

    $levels = Get-FirewallLevels
    $allowedPorts = @()
    $allowedPorts += $levels.Basic
    if ($Level -in @("Moderate", "Relaxed")) { $allowedPorts += $levels.Moderate }
    if ($Level -eq "Relaxed") { $allowedPorts += $levels.Extended }

    foreach ($rule in $allowedPorts) {
        try {
            $ports = if ($rule.Port -is [array]) { $rule.Port -join "," } else { $rule.Port }
            New-NetFirewallRule -DisplayName "OpenGuard-Adaptive-Allow $($rule.Name)" -Direction Outbound -Action Allow -Protocol $rule.Protocol -RemotePort $ports -Profile Public -Enabled $true -ErrorAction Stop | Out-Null
            Write-Host "  ✓ $($rule.Name) ($($rule.Protocol)/$($rule.Port))" -ForegroundColor Green
        }
        catch { Write-Host "  ✗ $($rule.Name) - Hata" -ForegroundColor Red }
    }

    if ($Level -eq "Basic") {
        New-NetFirewallRule -DisplayName "OpenGuard-Adaptive-Block All Other" -Direction Outbound -Action Block -Profile Public -Enabled $true -ErrorAction SilentlyContinue | Out-Null
        Write-Host ""
        Write-Host "  [!] Basic mod: Diger tum cikislar engellendi" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "  Toplam kural: $($allowedPorts.Count)" -ForegroundColor Cyan
    Write-Host ""
}

function Show-FirewallStatus {
    $rules = @(Get-NetFirewallRule -DisplayName "OpenGuard-Adaptive*" -ErrorAction SilentlyContinue)
    $current = if ($rules | Where-Object { $_.DisplayName -like "*Block All*" }) { "Basic" } elseif ($rules.Count -gt 6) { "Relaxed" } else { "Moderate" }

    Write-Host ""
    Write-Host "  Firewall Durumu:" -ForegroundColor Cyan
    Write-Host "  Mod      : $current"
    Write-Host "  Kural    : $($rules.Count)"
    Write-Host ""
}

# ============================================
# DNSSecurityCheck - Inline (v0.5.0)
# ============================================
$TrustedDNS = @{
    "1.1.1.1" = "Cloudflare"
    "1.0.0.1" = "Cloudflare"
    "8.8.8.8" = "Google"
    "8.8.4.4" = "Google"
    "9.9.9.9" = "Quad9"
    "149.112.112.112" = "Quad9"
    "208.67.222.222" = "OpenDNS"
}

function Test-DNSSecurity {
    Write-Host ""
    Write-Host "  ========================================" -ForegroundColor Cyan
    Write-Host "  DNS Guvenligi Kontrol Sonuclari" -ForegroundColor White
    Write-Host "  ========================================" -ForegroundColor Cyan
    Write-Host ""

    $dnsServers = @()
    try {
        $adapters = Get-NetAdapter | Where-Object Status -eq "Up"
        foreach ($adapter in $adapters) {
            $dns = Get-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -ErrorAction SilentlyContinue
            $dnsServers += $dns.ServerAddresses
        }
    }
    catch {}

    if (-not $dnsServers -or $dnsServers.Count -eq 0) {
        Write-Host "  [!] DNS sunucusu bulunamadi" -ForegroundColor Yellow
        return
    }

    $untrusted = @()
    foreach ($dns in $dnsServers) {
        if ([string]::IsNullOrEmpty($dns)) { continue }
        if ($TrustedDNS.ContainsKey($dns)) {
            $provider = $TrustedDNS[$dns]
            Write-Host "  ✓ $dns ($provider)" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠ $dns (Bilinmeyen)" -ForegroundColor Yellow
            $untrusted += $dns
        }
    }

    Write-Host ""
    Write-Host "  HTTPS Bazli DNS Guvenligi:" -ForegroundColor Cyan

    $dohSupported = Test-DoHAvailability
    if ($dohSupported) {
        Write-Host "  ✓ DoH (DNS over HTTPS) Kullanilabilir" -ForegroundColor Green
        Write-Host "    Tavsiye: Tarayici DoH etkinlestirin" -ForegroundColor DarkGray
    }
    else {
        Write-Host "  ⚠ DoH Bulunamadi" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "  Risk Degerlendirmesi:" -ForegroundColor Cyan
    if ($untrusted.Count -gt 0) {
        Write-Host "  [!] $($untrusted.Count) bilinmeyen DNS servisi" -ForegroundColor Red
    }
    else {
        Write-Host "  ✓ Tum DNS sunuculari guvenilir" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "  Oneriler:" -ForegroundColor Cyan
    Write-Host "  1. Cloudflare/Quad9/Google DNS kullanin" -ForegroundColor DarkGray
    Write-Host "  2. Tarayici DoH etkinlestirin" -ForegroundColor DarkGray
    Write-Host "  3. VPN ile birlikte kullanin" -ForegroundColor DarkGray
    Write-Host ""
}

function Test-DoHAvailability {
    $dohServers = @("https://cloudflare-dns.com/dns-query", "https://dns.quad9.net/dns-query")
    foreach ($server in $dohServers) {
        try {
            $response = Invoke-WebRequest -Uri $server -Method HEAD -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) { return $true }
        }
        catch {}
    }
    return $false
}

# ============================================
# Analytics Dashboard - Inline (v0.6.0)
# ============================================
function Get-AnalyticsData {
    $logDir = Join-Path $env:APPDATA "OpenGuard"
    $logFile = Join-Path $logDir "security_log.jsonl"

    if (-not (Test-Path $logFile)) {
        return $null
    }

    $logs = @()
    try {
        Get-Content $logFile | ForEach-Object {
            if (-not [string]::IsNullOrEmpty($_)) {
                $logs += $_ | ConvertFrom-Json
            }
        }
    }
    catch {}

    return $logs
}

function Show-AnalyticsDashboard {
    Write-Host ""
    Write-Host "  ========================================" -ForegroundColor Cyan
    Write-Host "  OpenGuard Analytics Dashboard (v0.6.0)" -ForegroundColor White
    Write-Host "  ========================================" -ForegroundColor Cyan
    Write-Host ""

    $logs = Get-AnalyticsData

    if (-not $logs -or $logs.Count -eq 0) {
        Write-Host "  Log yok henuz. Hardening'i bir kez acin." -ForegroundColor Yellow
        Write-Host ""
        return
    }

    # Statistics
    Write-Host "  --- Istatistikler ---" -ForegroundColor Yellow
    Write-Host "  Toplam event: $($logs.Count)"

    $hardeningOn = $logs | Where-Object { $_.Event -like "*Activ*" } | Measure-Object
    Write-Host "  Hardening acildi: $($hardeningOn.Count) kez"

    $threats = $logs | Where-Object { $_.Event -like "*Threat*" } | Measure-Object
    Write-Host "  Tehdit uyarisi: $($threats.Count) kez"

    # Recent events
    Write-Host ""
    Write-Host "  --- Son Olaylar (Son 5) ---" -ForegroundColor Cyan

    $recentLogs = $logs | Sort-Object { [datetime]$_.Timestamp } -Descending | Select-Object -First 5

    foreach ($log in $recentLogs) {
        $ts = $log.Timestamp
        $event = $log.Event
        $severity = $log.Severity

        $color = switch ($severity) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "SUCCESS" { "Green" }
            default { "Cyan" }
        }

        Write-Host "  [$ts] [$severity] $event" -ForegroundColor $color
    }

    # Threat Timeline
    Write-Host ""
    Write-Host "  --- Tehdit Zaman Tabelosu ---" -ForegroundColor Magenta

    $threats = $logs | Where-Object { $_.Severity -eq "ERROR" -or $_.Severity -eq "WARN" }

    if ($threats.Count -eq 0) {
        Write-Host "  Tehdit yok. Guvenli!" -ForegroundColor Green
    }
    else {
        foreach ($threat in $threats | Sort-Object { [datetime]$_.Timestamp } -Descending | Select-Object -First 10) {
            $ts = $threat.Timestamp
            $event = $threat.Event
            Write-Host "  [$ts] ! $event" -ForegroundColor Yellow
        }
    }

    # Risk Summary
    Write-Host ""
    Write-Host "  --- Risk Ozeti ---" -ForegroundColor Magenta

    $last24h = $logs | Where-Object {
        [datetime]$_.Timestamp -gt (Get-Date).AddHours(-24)
    }

    if ($last24h.Count -eq 0) {
        Write-Host "  Son 24 saat: DUSUK (Veri yok)" -ForegroundColor Green
    }
    else {
        $riskCount = ($last24h | Where-Object { $_.Severity -in @("ERROR", "WARN") } | Measure-Object).Count

        if ($riskCount -eq 0) {
            Write-Host "  Son 24 saat: DUSUK - Tehdit yok" -ForegroundColor Green
        }
        elseif ($riskCount -le 2) {
            Write-Host "  Son 24 saat: ORTA - Birkaç uyarı" -ForegroundColor Yellow
        }
        else {
            Write-Host "  Son 24 saat: YUKSEK - $riskCount olay kaydedildi" -ForegroundColor Red
        }
    }

    Write-Host ""
}
$RulePrefix = "OpenGuard-Hardening"
$ConfigDir  = Join-Path $env:APPDATA "OpenGuard"
$ConfigFile = Join-Path $ConfigDir "config.txt"
$WatchFile  = Join-Path $env:TEMP "OpenGuard-GatewayBaseline.txt"

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Only relaunch for the interactive user. Re-elevating does not carry -Action
# through, so a programmatic call would silently open a menu window and report
# success; in that mode a missing privilege must fail loudly instead.
if (-not $Action -and -not (Test-IsAdmin)) {
    Write-Host ""
    Write-Host "  Yonetici yetkisi gerekiyor. Yeniden baslatiliyor..." -ForegroundColor Yellow
    $scriptPath = $MyInvocation.MyCommand.Definition
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
    exit
}

function Write-OG {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "HH:mm:ss"
    $color = switch ($Level) {
        "SUCCESS" { "Green" }
        "WARN"    { "Yellow" }
        "ERROR"   { "Red" }
        default   { "Cyan" }
    }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

function Pause-OG {
    Write-Host ""
    Write-Host "  Devam etmek icin bir tusa basin..." -ForegroundColor DarkGray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

function Get-CurrentNetworkProfiles {
    Get-NetConnectionProfile | Select-Object Name, InterfaceAlias, NetworkCategory, IPv4Connectivity
}

function Set-NetworkToPublic {
    $profiles = Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -ne "DomainAuthenticated" }
    foreach ($p in $profiles) {
        try {
            Set-NetConnectionProfile -InterfaceIndex $p.InterfaceIndex -NetworkCategory Public -ErrorAction Stop
            Write-OG "Ag profili Public yapildi -> $($p.Name)" "SUCCESS"
        } catch {
            Write-OG "Profil degistirilemedi: $($p.Name)" "WARN"
        }
    }
}

function Disable-NetworkDiscoveryAndSharing {
    $groups = @("Network Discovery", "File and Printer Sharing", "File and Printer Sharing over SMBDirect")
    foreach ($g in $groups) {
        $rules = Get-NetFirewallRule -DisplayGroup $g -ErrorAction SilentlyContinue
        if ($rules) {
            $rules | Set-NetFirewallRule -Enabled False -ErrorAction SilentlyContinue
            Write-OG "Firewall grubu kapatildi: $g" "INFO"
        }
    }
    foreach ($svcName in @("FDResPub", "SSDPSRV", "upnphost")) {
        $s = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($s -and $s.Status -eq "Running") {
            try {
                Stop-Service -Name $svcName -Force -ErrorAction Stop
                Set-Service -Name $svcName -StartupType Manual -ErrorAction SilentlyContinue
                Write-OG "Servis durduruldu: $svcName" "INFO"
            } catch {
                Write-OG "Servis islenemedi: $svcName" "WARN"
            }
        }
    }
}

function Disable-LLMNR {
    $regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"
    if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
    Set-ItemProperty -Path $regPath -Name "EnableMulticast" -Value 0 -Type DWord -Force
    Write-OG "LLMNR kapatildi" "INFO"
}

function Disable-NetBIOS {
    $adapters = Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" -ErrorAction SilentlyContinue
    if (-not $adapters) {
        $adapters = Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled }
    }
    foreach ($a in $adapters) {
        try {
            $a.SetTcpipNetbios(2) | Out-Null
            Write-OG "NetBIOS kapatildi -> $($a.Description)" "INFO"
        } catch {
            Write-OG "NetBIOS kapatilamadi: $($a.Description)" "WARN"
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
        }
    }
}

function Enable-AggressiveMode {
    Write-OG "Agresif mod uygulanıyor..." "WARN"
    Get-NetFirewallRule -DisplayName "$RulePrefix-Agg*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Allow DNS UDP" -Direction Outbound -Action Allow -Protocol UDP -RemotePort 53 -Profile Public -Enabled True | Out-Null
    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Allow DNS TCP" -Direction Outbound -Action Allow -Protocol TCP -RemotePort 53 -Profile Public -Enabled True | Out-Null
    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Allow HTTP"  -Direction Outbound -Action Allow -Protocol TCP -RemotePort 80  -Profile Public -Enabled True | Out-Null
    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Allow HTTPS" -Direction Outbound -Action Allow -Protocol TCP -RemotePort 443 -Profile Public -Enabled True | Out-Null
    New-NetFirewallRule -DisplayName "$RulePrefix-Agg Block All Other" -Direction Outbound -Action Block -Profile Public -Enabled True | Out-Null
    Write-OG "Agresif kurallar eklendi" "SUCCESS"
}

function Remove-AggressiveRules {
    Get-NetFirewallRule -DisplayName "$RulePrefix-Agg*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
}

function Enable-Hardening {
    param([switch]$Aggressive)
    Write-Host ""
    Write-OG "Hardening baslatiliyor..." "INFO"
    Write-Host ""
    Write-Host "  =============================================" -ForegroundColor Yellow
    Write-Host "  RISK UYARISI" -ForegroundColor Yellow
    Write-Host "  Bu arac trafigi sifrelemez." -ForegroundColor Yellow
    Write-Host "  Dinleme ve MITM riskini ortadan kaldirmaz." -ForegroundColor Yellow
    Write-Host "  Sadece cihazin kesfedilmesini zorlastirir." -ForegroundColor Yellow
    Write-Host "  =============================================" -ForegroundColor Yellow
    Write-Host ""
    Set-NetworkToPublic
    Disable-NetworkDiscoveryAndSharing
    Disable-LLMNR
    Disable-NetBIOS
    Set-FirewallPublicTight
    if ($Aggressive) { Enable-AggressiveMode }
    Write-Host ""
    Write-OG "Hardening tamamlandi." "SUCCESS"
}

function Restore-Defaults {
    Write-OG "Sertlestirmeler geri aliniyor..." "INFO"
    $regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"
    if (Test-Path $regPath) {
        Remove-ItemProperty -Path $regPath -Name "EnableMulticast" -ErrorAction SilentlyContinue
        Write-OG "LLMNR ayari kaldirildi" "INFO"
    }
    $adapters = Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -Filter "IPEnabled = True" -ErrorAction SilentlyContinue
    if (-not $adapters) {
        $adapters = Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled }
    }
    foreach ($a in $adapters) {
        try { $a.SetTcpipNetbios(0) | Out-Null } catch {}
    }
    Write-OG "NetBIOS varsayilana donduruldu" "INFO"
    foreach ($svcName in @("FDResPub", "SSDPSRV", "upnphost")) {
        $s = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($s) { Set-Service -Name $svcName -StartupType Manual -ErrorAction SilentlyContinue }
    }
    foreach ($g in @("Network Discovery", "File and Printer Sharing")) {
        Get-NetFirewallRule -DisplayGroup $g -ErrorAction SilentlyContinue |
            Set-NetFirewallRule -Enabled True -ErrorAction SilentlyContinue
    }
    Remove-AggressiveRules
    Write-OG "Sertlestirmeler geri alindi." "SUCCESS"
}

function Show-Status {
    Write-Host ""
    Write-Host "  Mevcut ag profilleri:" -ForegroundColor Cyan
    Get-CurrentNetworkProfiles | Format-Table -AutoSize
    $llmnr = Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Name "EnableMulticast" -ErrorAction SilentlyContinue
    if ($llmnr -and $llmnr.EnableMulticast -eq 0) {
        Write-Host "  LLMNR          : KAPALI" -ForegroundColor Green
    } else {
        Write-Host "  LLMNR          : Açık / Varsayılan" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "  Ilgili servisler:" -ForegroundColor Cyan
    foreach ($svcName in @("FDResPub", "SSDPSRV", "upnphost")) {
        $s = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($s) {
            $color = if ($s.Status -eq "Running") { "Yellow" } else { "Green" }
            Write-Host ("  {0,-12} : {1,-10} ({2})" -f $svcName, $s.Status, $s.StartType) -ForegroundColor $color
        }
    }
    $agg = Get-NetFirewallRule -DisplayName "$RulePrefix-Agg*" -ErrorAction SilentlyContinue
    Write-Host ""
    if ($agg) {
        Write-Host "  Agresif mod    : AKTIF" -ForegroundColor Yellow
    } else {
        Write-Host "  Agresif mod    : Kapalı" -ForegroundColor DarkGray
    }
    Write-Host ""
}

function Get-GatewayInfo {
    try {
        $route = Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue |
                 Where-Object { $_.NextHop -and $_.NextHop -ne "0.0.0.0" } |
                 Select-Object -First 1
        if (-not $route) { return $null }
        $neighbor = Get-NetNeighbor -IPAddress $route.NextHop -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $neighbor) { return $null }
        return [PSCustomObject]@{ IP = $route.NextHop; MAC = $neighbor.LinkLayerAddress }
    } catch { return $null }
}

function Save-GatewayBaseline {
    $info = Get-GatewayInfo
    if (-not $info) {
        Write-OG "Ag gecidi bilgisi alinamadi." "WARN"
        return
    }
    $line = "$($info.IP)|$($info.MAC)|$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Set-Content -Path $WatchFile -Value $line -Encoding UTF8
    Write-OG "Temel deger kaydedildi: $($info.IP) / $($info.MAC)" "SUCCESS"
}

function Get-GatewayBaseline {
    if (-not (Test-Path $WatchFile)) { return $null }
    $line = Get-Content $WatchFile -Raw -ErrorAction SilentlyContinue
    if (-not $line) { return $null }
    $parts = $line.Trim() -split "\|"
    if ($parts.Count -lt 2) { return $null }
    return [PSCustomObject]@{ IP = $parts[0]; MAC = $parts[1] }
}

function Test-FailedLogons {
    try {
        $start = (Get-Date).AddMinutes(-30)
        $events = Get-WinEvent -FilterHashtable @{ LogName = "Security"; Id = 4625; StartTime = $start } -ErrorAction SilentlyContinue
        if ($events) { return $events.Count }
    } catch {}
    return 0
}

function Show-ThreatWarning {
    Write-Host ""
    Write-Host "  #####################################################" -ForegroundColor Red
    Write-Host "  #  UYARI                                            #" -ForegroundColor Red
    Write-Host "  #  Kesin olmamakla beraber bilgisayarınıza          #" -ForegroundColor Yellow
    Write-Host "  #  dışarıdan müdahale etmeye çalışıldığına dair     #" -ForegroundColor Yellow
    Write-Host "  #  belirtiler var.                                  #" -ForegroundColor Yellow
    Write-Host "  #  Hemen bağlanmış olduğunuz kablosuz ağ            #" -ForegroundColor Yellow
    Write-Host "  #  bağlantısını kesmenizi tavsiye ediyoruz.         #" -ForegroundColor Yellow
    Write-Host "  #####################################################" -ForegroundColor Red
    Write-Host ""
}

function Invoke-NetworkWatch {
    Write-Host ""
    Write-Host "  --- Ag Izleme / Uyari ---" -ForegroundColor Cyan
    Write-Host ""
    $current = Get-GatewayInfo
    if (-not $current) {
        Write-OG "Su an ag gecidi bilgisi alinamadi. Wi-Fi bagli mi?" "WARN"
        return
    }
    Write-Host "  Mevcut ag gecidi : $($current.IP)" -ForegroundColor White
    Write-Host "  Mevcut MAC       : $($current.MAC)" -ForegroundColor White
    Write-Host ""
    $baseline = Get-GatewayBaseline
    $suspicious = $false
    if (-not $baseline) {
        Write-OG "Henuz temel deger yok. Simdi kaydediliyor..." "INFO"
        Save-GatewayBaseline
        Write-Host ""
        Write-Host "  Ilk kayit alindi. Sonraki kontrollerde degisim olursa uyaracagiz." -ForegroundColor DarkGray
        return
    }
    Write-Host "  Kayitli MAC      : $($baseline.MAC)" -ForegroundColor DarkGray
    Write-Host ""
    if ($current.MAC -ne $baseline.MAC) {
        Write-OG "AG GECIDI MAC ADRESI DEGISMIS!" "ERROR"
        $suspicious = $true
    } else {
        Write-OG "Ag gecidi MAC adresi degismemis (normal)." "SUCCESS"
    }
    $failCount = Test-FailedLogons
    if ($failCount -gt 0) {
        Write-OG "Son 30 dakikada $failCount basarisiz oturum acma denemesi var." "WARN"
        if ($failCount -ge 3) { $suspicious = $true }
    } else {
        Write-OG "Son 30 dakikada basarisiz oturum acma kaydi yok." "INFO"
    }
    if ($suspicious) { Show-ThreatWarning }
    else {
        Write-Host ""
        Write-Host "  Su an belirgin bir anormallik gorunmuyor." -ForegroundColor Green
        Write-Host ""
    }
}

function Get-DefaultConfig {
    return @{
        Mode            = "SemiAuto"
        AutoHardening   = "Yes"
        AutoWatch       = "No"
        ReminderEnabled = "Yes"
        ReminderMinutes = "15"
    }
}

function Load-Config {
    $cfg = Get-DefaultConfig
    if (-not (Test-Path $ConfigFile)) { return $cfg }
    try {
        Get-Content $ConfigFile -Encoding UTF8 | ForEach-Object {
            if ($_ -match "^\s*([^#=]+)=(.*)$") {
                $k = $matches[1].Trim()
                $v = $matches[2].Trim()
                if ($cfg.ContainsKey($k)) { $cfg[$k] = $v }
            }
        }
    } catch {}
    return $cfg
}

function Save-Config($cfg) {
    if (-not (Test-Path $ConfigDir)) {
        New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    }
    $lines = @(
        "Mode=$($cfg.Mode)",
        "AutoHardening=$($cfg.AutoHardening)",
        "AutoWatch=$($cfg.AutoWatch)",
        "ReminderEnabled=$($cfg.ReminderEnabled)",
        "ReminderMinutes=$($cfg.ReminderMinutes)"
    )
    Set-Content -Path $ConfigFile -Value $lines -Encoding UTF8
    Write-OG "Ayarlar kaydedildi." "SUCCESS"
}

function Test-IsPublicNetwork {
    $profiles = Get-NetConnectionProfile -ErrorAction SilentlyContinue
    foreach ($p in $profiles) {
        if ($p.NetworkCategory -eq "Public") { return $true }
    }
    return $false
}

function Test-IsHardeningActive {
    # Only OpenGuard creates firewall rules under this prefix, so their presence
    # is the one signal that unambiguously means this tool applied hardening.
    #
    # LLMNR alone used to answer this, which was wrong: group policy or another
    # security product can disable LLMNR, and OpenGuard would then report that
    # as its own protection on a machine where it had never run.
    $rules = Get-NetFirewallRule -DisplayName "OpenGuard-*" -ErrorAction SilentlyContinue
    if ($rules) { return $true }

    return $false
}

function Invoke-SemiAutoCheck {
    $cfg = Load-Config
    if ($cfg.Mode -eq "Manual") { return }
    if (-not (Test-IsPublicNetwork)) { return }
    $hardeningOn = Test-IsHardeningActive
    if ($cfg.Mode -eq "SemiAuto") {
        if (-not $hardeningOn -and $cfg.AutoHardening -eq "Yes") {
            Write-Host ""
            Write-Host "  =============================================" -ForegroundColor Yellow
            Write-Host "  Public ag algilandi." -ForegroundColor Yellow
            Write-Host "  OpenGuard Hardening su an kapali." -ForegroundColor Yellow
            Write-Host "  =============================================" -ForegroundColor Yellow
            Write-Host ""
            $cevap = Read-Host "  Hardening simdi acilsin mi? (E/H)"
            if ($cevap -eq "E" -or $cevap -eq "e") {
                Enable-Hardening
            } else {
                Write-OG "Hardening acilmadi. Isterseniz menuden acabilirsiniz." "INFO"
            }
        }
    }
    elseif ($cfg.Mode -eq "FullAuto") {
        if (-not $hardeningOn -and $cfg.AutoHardening -eq "Yes") {
            Write-OG "Tam otomatik: Public ag - Hardening aciliyor..." "WARN"
            Enable-Hardening
        }
        if ($cfg.AutoWatch -eq "Yes") { Invoke-NetworkWatch }
    }
}

function Show-Settings {
    $cfg = Load-Config
    Clear-Host
    Write-Host ""
    Write-Host "  --- Ayarlar ---" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1) Calisma modu        : $($cfg.Mode)" -ForegroundColor White
    Write-Host "     (Manual / SemiAuto / FullAuto)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  2) Otomatik Hardening  : $($cfg.AutoHardening)" -ForegroundColor White
    Write-Host "  3) Otomatik Ag Izleme  : $($cfg.AutoWatch)" -ForegroundColor White
    Write-Host "  4) Hatirlatma          : $($cfg.ReminderEnabled) (her $($cfg.ReminderMinutes) dk)" -ForegroundColor White
    Write-Host ""
    Write-Host "  5) Kaydet ve geri don" -ForegroundColor Green
    Write-Host "  6) Iptal" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Not: Agresif Mod hicbir zaman otomatik acilmaz." -ForegroundColor DarkYellow
    Write-Host ""
    $sec = Read-Host "  Seciminiz"
    switch ($sec) {
        "1" {
            Write-Host ""
            Write-Host "  Manual   = Sadece elle acarsiniz"
            Write-Host "  SemiAuto = Public agda sorar (onerilen)"
            Write-Host "  FullAuto = Public agda kendisi acar"
            Write-Host ""
            $m = Read-Host "  Yeni mod (Manual/SemiAuto/FullAuto)"
            if ($m -in @("Manual","SemiAuto","FullAuto")) {
                $cfg.Mode = $m
                Save-Config $cfg
            } else {
                Write-OG "Gecersiz mod." "WARN"
            }
            Pause-OG
            Show-Settings
        }
        "2" {
            $cfg.AutoHardening = if ($cfg.AutoHardening -eq "Yes") { "No" } else { "Yes" }
            Save-Config $cfg
            Pause-OG
            Show-Settings
        }
        "3" {
            $cfg.AutoWatch = if ($cfg.AutoWatch -eq "Yes") { "No" } else { "Yes" }
            Save-Config $cfg
            Pause-OG
            Show-Settings
        }
        "4" {
            $cfg.ReminderEnabled = if ($cfg.ReminderEnabled -eq "Yes") { "No" } else { "Yes" }
            Save-Config $cfg
            Pause-OG
            Show-Settings
        }
        "5" { Save-Config $cfg }
        "6" { return }
        default {
            Write-OG "Gecersiz secim." "WARN"
            Pause-OG
            Show-Settings
        }
    }
}

function Show-Help {
    Clear-Host
    Write-Host ""
    Write-Host "  --- Kullanim Kilavuzu, Riskler ve Uyarilar ---" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1) Hardening'i Ac (Secenek 2)" -ForegroundColor Green
    Write-Host "     Bilgisayari halka acik aglara karsi daha kapali hale getirir."
    Write-Host "     Ne zaman: Kahveci zincirleri, restoranlar, kafeler, otel,"
    Write-Host "     havalimani, otogar, sehir meydani, kamu kurumlari gibi"
    Write-Host "     halka acik aglara baglandiginizda."
    Write-Host ""
    Write-Host "  2) Hardening'i Kapat (Secenek 3)" -ForegroundColor Yellow
    Write-Host "     Degisiklikleri geri alir. Eve donunce kullanin."
    Write-Host ""
    Write-Host "  3) Agresif Mod (Secenek 4)" -ForegroundColor Red
    Write-Host "     Cok siki kural. Bircok program bozulabilir. Otomatik acilmaz."
    Write-Host ""
    Write-Host "  4) Ag Izleme (Secenek 6)" -ForegroundColor Magenta
    Write-Host "     Ag gecidi MAC degisimi ve basarisiz oturum denemelerini kontrol eder."
    Write-Host ""
    Write-Host "  NE ISE YARAMAZ?" -ForegroundColor Red
    Write-Host "  - Trafigi sifrelemez"
    Write-Host "  - Dinleme / MITM riskini ortadan kaldirmaz"
    Write-Host "  - Zararli yazilimlara karsi koruma saglamaz"
    Write-Host ""
    Write-Host "  RISK UYARISI" -ForegroundColor Red
    Write-Host "  Bu arac sadece saldiri yuzeyini kucultur."
    Write-Host "  Hassas islemler icin halka acik aglardan kacinin."
    Write-Host "  Gercek koruma icin sifreli tunnel (VPN) gerekir."
    Write-Host ""
}

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "  ==========================================" -ForegroundColor DarkCyan
    Write-Host "         OpenGuard Hardening v$Version" -ForegroundColor White
    Write-Host "  ==========================================" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "  1) Durum Tespiti" -ForegroundColor White
    Write-Host "  2) Hardening'i Ac" -ForegroundColor Green
    Write-Host "  3) Hardening'i Kapat" -ForegroundColor Yellow
    Write-Host "  4) Agresif Mod ile Ac" -ForegroundColor Red
    Write-Host "  5) Adaptive Firewall" -ForegroundColor Cyan
    Write-Host "  6) DNS Guvenligi" -ForegroundColor Cyan
    Write-Host "  7) Ag Izleme / Uyari" -ForegroundColor Magenta
    Write-Host "  8) Kullanim Kilavuzu" -ForegroundColor White
    Write-Host "  9) Ayarlar" -ForegroundColor White
    Write-Host "  10) [YENİ] Analytics Dashboard" -ForegroundColor Green
    Write-Host "  11) Cikis" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  OpenGuard trafigi sifrelemez." -ForegroundColor DarkYellow
    Write-Host "  Sadece saldiri yuzeyini kucultur." -ForegroundColor DarkYellow
    Write-Host ""
}

# --- Non-interactive entry point ---
# Placed after every function definition and before anything that prompts or
# draws, so a programmatic call never reaches the menu loop.
if ($Action) {
    if (-not (Test-IsAdmin)) {
        Write-Error "OpenGuard requires Administrator privileges."
        exit 2
    }

    try {
        switch ($Action) {
            "Enable" {
                Enable-Hardening
                Enable-AdaptiveRules -Level $Level
                exit 0
            }
            "Disable" {
                Restore-Defaults
                exit 0
            }
            "Status" {
                # Exit code is the answer: 0 active, 1 inactive.
                if (Test-IsHardeningActive) { exit 0 } else { exit 1 }
            }
        }
    }
    catch {
        Write-Error $_.Exception.Message
        exit 3
    }
}

# --- Baslangic: yari otomatik kontrol ---
Invoke-SemiAutoCheck

# --- Ana dongu ---
do {
    Show-Menu
    $choice = Read-Host "  Seciminiz (1-11)"
    switch ($choice) {
        "1" {
            Clear-Host
            Write-Host ""
            Write-Host "  --- Durum ---" -ForegroundColor Cyan
            Show-Status
            Pause-OG
        }
        "2" {
            Clear-Host
            Enable-Hardening
            Pause-OG
        }
        "3" {
            Clear-Host
            Restore-Defaults
            Pause-OG
        }
        "4" {
            Clear-Host
            Write-Host ""
            Write-Host "  DIKKAT: Agresif mod bircok uygulamayi bozabilir!" -ForegroundColor Red
            Write-Host "  Sadece gercekten gerektiginde kullanin." -ForegroundColor Red
            Write-Host ""
            $onay = Read-Host "  Devam etmek istiyor musunuz? (E/H)"
            if ($onay -eq "E" -or $onay -eq "e") {
                Enable-Hardening -Aggressive
            } else {
                Write-OG "Iptal edildi." "INFO"
            }
            Pause-OG
        }
        "5" {
            # Adaptive Firewall (YENİ v0.5.0)
            Clear-Host
            Write-Host ""
            Write-Host "  Firewall Seviyeleri:" -ForegroundColor Cyan
            Write-Host "  1) Basic (Sadece web+DNS)" -ForegroundColor Red
            Write-Host "  2) Moderate (Onemlenir)" -ForegroundColor Green
            Write-Host "  3) Relaxed (Daha cok port)" -ForegroundColor Yellow
            Write-Host ""
            $fw = Read-Host "  Secenek (1-3)"
            $levels = @{"1" = "Basic"; "2" = "Moderate"; "3" = "Relaxed"}
            if ($levels.ContainsKey($fw)) {
                Enable-AdaptiveRules -Level $levels[$fw]
            }
            Show-FirewallStatus
            Pause-OG
        }
        "6" {
            # DNS Security (YENİ v0.5.0)
            Clear-Host
            Test-DNSSecurity
            Write-Host ""
            $detail = Read-Host "  Detay goster? (E/H)"
            if ($detail -eq "E" -or $detail -eq "e") {
                Enable-DoHInBrowser
                Get-DNSLeakTest
            }
            Pause-OG
        }
        "7" {
            Clear-Host
            Invoke-NetworkWatch
            Pause-OG
        }
        "8" {
            Show-Help
            Pause-OG
        }
        "9" {
            Show-Settings
        }
        "10" {
            # Analytics Dashboard (YENİ v0.6.0)
            Clear-Host
            Show-AnalyticsDashboard
            Pause-OG
        }
        "11" {
            Write-Host ""
            Write-Host "  Gorusuruz." -ForegroundColor DarkGray
            Write-Host ""
            exit
        }
        default {
            Write-Host ""
            Write-Host "  Gecersiz secim." -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
} while ($true)