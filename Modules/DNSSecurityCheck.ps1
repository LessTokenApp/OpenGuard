# DNSSecurityCheck.ps1 - v0.5.0
# DNS Security Analysis & DoH Detection

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
    Write-Host " ========================================" -ForegroundColor Cyan
    Write-Host " DNS Guvenligi Kontrol Sonuclari" -ForegroundColor White
    Write-Host " ========================================" -ForegroundColor Cyan
    Write-Host ""

    # Get current DNS servers
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
        Write-Host " [!] DNS sunucusu bulunamadi" -ForegroundColor Yellow
        return
    }

    # Analyze each DNS server
    $untrusted = @()
    $trusted = @()

    foreach ($dns in $dnsServers) {
        if ([string]::IsNullOrEmpty($dns)) { continue }

        if ($TrustedDNS.ContainsKey($dns)) {
            $provider = $TrustedDNS[$dns]
            Write-Host " ✓ $dns ($provider)" -ForegroundColor Green
            $trusted += $dns
        }
        else {
            Write-Host " ⚠ $dns (Bilinmeyen)" -ForegroundColor Yellow
            $untrusted += $dns
        }
    }

    # DoH Support Check
    Write-Host ""
    Write-Host " HTTPS Bazli DNS Guvenligi:" -ForegroundColor Cyan

    $dohSupported = Test-DoHAvailability
    if ($dohSupported) {
        Write-Host " ✓ DoH (DNS over HTTPS) Kullanilabilir" -ForegroundColor Green
        Write-Host "   Tavsiye: Tarayici ayarlarindan DoH etkinlestirin" -ForegroundColor DarkGray
    }
    else {
        Write-Host " ⚠ DoH Bulunamadi" -ForegroundColor Yellow
    }

    # Risk Assessment
    Write-Host ""
    Write-Host " Risk Degerlendirmesi:" -ForegroundColor Cyan

    if ($untrusted.Count -gt 0) {
        Write-Host " [!] $($untrusted.Count) bilinmeyen DNS servisi" -ForegroundColor Red
        Write-Host "     DNS sizintisi ve hijacking riski olabilir" -ForegroundColor DarkGray
    }
    else {
        Write-Host " ✓ Tum DNS sunuculari guvenilir" -ForegroundColor Green
    }

    # Recommendations
    Write-Host ""
    Write-Host " Oneriler:" -ForegroundColor Cyan
    Write-Host " 1. Cloudflare, Quad9 veya Google DNS kullanin" -ForegroundColor DarkGray
    Write-Host " 2. Tarayici DoH etkinlestirin (Firefox, Edge)" -ForegroundColor DarkGray
    Write-Host " 3. VPN ile birlikte kullanin" -ForegroundColor DarkGray
    Write-Host " 4. Halka acik Wi-Fi'de hassas islem yapmayin" -ForegroundColor DarkGray
    Write-Host ""
}

function Test-DoHAvailability {
    $dohServers = @(
        "https://cloudflare-dns.com/dns-query",
        "https://dns.quad9.net/dns-query"
    )

    foreach ($server in $dohServers) {
        try {
            $response = Invoke-WebRequest -Uri $server -Method HEAD -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                return $true
            }
        }
        catch {}
    }

    return $false
}

function Enable-DoHInBrowser {
    Write-Host ""
    Write-Host " --- Firefox'te DoH Etkinlestirme ---" -ForegroundColor Cyan
    Write-Host " 1. Firefox Ayarlar > Gizlilik" -ForegroundColor DarkGray
    Write-Host " 2. DNS over HTTPS bolumune git" -ForegroundColor DarkGray
    Write-Host " 3. 'Max Protection' veya 'Standard' sec" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host " --- Edge/Chrome'te HTTPS DNS ---" -ForegroundColor Cyan
    Write-Host " 1. Ayarlar > Gizlilik ve guvenlik" -ForegroundColor DarkGray
    Write-Host " 2. Guvenli DNS ayarla > Cloudflare sec" -ForegroundColor DarkGray
    Write-Host ""
}

function Get-DNSLeakTest {
    Write-Host ""
    Write-Host " DNS Sizintisi Testi:" -ForegroundColor Cyan
    Write-Host " https://dnsleaktest.com" -ForegroundColor DarkGray
    Write-Host " (VPN'siz halka acik Wi-Fi'de sizintalar gorulecektir)" -ForegroundColor Yellow
    Write-Host ""
}
