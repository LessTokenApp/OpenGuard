# Analytics Dashboard v0.6.0
# OpenGuard Threat Timeline & Statistics

function Get-AnalyticsData {
    $logDir = Join-Path $env:APPDATA "OpenGuard"
    $logFile = Join-Path $logDir "security_log.jsonl"

    if (-not (Test-Path $logFile)) {
        Write-Host "  Log dosyasi bulunamadi." -ForegroundColor Yellow
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
    catch {
        Write-Host "  Log okuma hatasi." -ForegroundColor Yellow
        return $null
    }

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
        Write-Host "  Log yok henuz. Hardening'i bir kez aciniz." -ForegroundColor Yellow
        Write-Host ""
        return
    }

    # Statistics
    Write-Host "  --- İstatistikler ---" -ForegroundColor Yellow
    Write-Host "  Toplam event: $($logs.Count)"

    $hardeningOn = $logs | Where-Object { $_.Event -like "*Activated*" -or $_.Event -like "*acildi*" } | Measure-Object
    Write-Host "  Hardening acildi: $($hardeningOn.Count) kez"

    $threats = $logs | Where-Object { $_.Event -like "*Threat*" -or $_.Event -like "*uyari*" } | Measure-Object
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
            Write-Host "  [$ts] ⚠ $event" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "  --- Risk Ozeti ---" -ForegroundColor Magenta
    Write-Host "  Son 24 saat risk skoru:" -ForegroundColor White

    $last24h = $logs | Where-Object {
        [datetime]$_.Timestamp -gt (Get-Date).AddHours(-24)
    }

    if ($last24h.Count -eq 0) {
        Write-Host "  DUSUK (Veri yok)" -ForegroundColor Green
    }
    else {
        $riskCount = ($last24h | Where-Object { $_.Severity -in @("ERROR", "WARN") } | Measure-Object).Count

        if ($riskCount -eq 0) {
            Write-Host "  DUSUK - Tehdit yok" -ForegroundColor Green
        }
        elseif ($riskCount -le 2) {
            Write-Host "  ORTA - Birkaç uyarı" -ForegroundColor Yellow
        }
        else {
            Write-Host "  YUKSEK - $riskCount olay kaydedildi" -ForegroundColor Red
        }
    }

    Write-Host ""
}

function Export-AnalyticsReport {
    param([string]$OutputPath)

    $logs = Get-AnalyticsData
    if (-not $logs) {
        Write-Host "  Export yapılamadı." -ForegroundColor Yellow
        return
    }

    try {
        $logs | ConvertTo-Json | Set-Content -Path $OutputPath -Encoding UTF8
        Write-Host "  Report kaydedildi: $OutputPath" -ForegroundColor Green
    }
    catch {
        Write-Host "  Export hatasi." -ForegroundColor Red
    }
}
