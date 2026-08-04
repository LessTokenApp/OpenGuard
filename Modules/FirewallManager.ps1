# FirewallManager.ps1 - v0.5.0
# Adaptive Firewall Rules: Basic / Moderate / Relaxed

$RulePrefix = "OpenGuard-Adaptive"

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
    param(
        [ValidateSet("Basic", "Moderate", "Relaxed")]
        [string]$Level = "Moderate"
    )

    Write-Host ""
    Write-Host " ========================================" -ForegroundColor Cyan
    Write-Host " Adaptive Firewall: $Level modu" -ForegroundColor White
    Write-Host " ========================================" -ForegroundColor Cyan
    Write-Host ""

    # Remove existing rules
    Get-NetFirewallRule -DisplayName "$RulePrefix*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue

    $levels = Get-FirewallLevels
    $allowedPorts = @()

    # Build rule list based on level
    $allowedPorts += $levels.Basic

    if ($Level -in @("Moderate", "Relaxed")) {
        $allowedPorts += $levels.Moderate
    }

    if ($Level -eq "Relaxed") {
        $allowedPorts += $levels.Extended
    }

    # Apply each rule
    foreach ($rule in $allowedPorts) {
        try {
            $ports = if ($rule.Port -is [array]) { $rule.Port -join "," } else { $rule.Port }

            New-NetFirewallRule `
                -DisplayName "$RulePrefix-Allow $($rule.Name)" `
                -Direction Outbound `
                -Action Allow `
                -Protocol $rule.Protocol `
                -RemotePort $ports `
                -Profile Public `
                -Enabled $true `
                -ErrorAction Stop | Out-Null

            Write-Host " ✓ $($rule.Name) ($($rule.Protocol)/$($rule.Port))" -ForegroundColor Green
        }
        catch {
            Write-Host " ✗ $($rule.Name) - Hata" -ForegroundColor Red
        }
    }

    # Block all other outbound if Basic mode
    if ($Level -eq "Basic") {
        New-NetFirewallRule `
            -DisplayName "$RulePrefix-Block All Other" `
            -Direction Outbound `
            -Action Block `
            -Profile Public `
            -Enabled $true `
            -ErrorAction SilentlyContinue | Out-Null

        Write-Host ""
        Write-Host " [!] Basic mod: Diger tum cikislar engellendi" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host " Toplam kural: $($allowedPorts.Count)" -ForegroundColor Cyan
    Write-Host ""
}

function Get-CurrentFirewallLevel {
    $rules = Get-NetFirewallRule -DisplayName "$RulePrefix*" -ErrorAction SilentlyContinue

    if (-not $rules) {
        return "None"
    }

    $blockAllRule = $rules | Where-Object { $_.DisplayName -like "*Block All Other*" }
    if ($blockAllRule) {
        return "Basic"
    }

    $extendedPorts = @(8080, 1194, 51820)
    $hasExtended = $false
    foreach ($port in $extendedPorts) {
        if ($rules.DisplayName -like "*$port*") {
            $hasExtended = $true
            break
        }
    }

    if ($hasExtended) {
        return "Relaxed"
    }

    return "Moderate"
}

function Remove-AdaptiveRules {
    Get-NetFirewallRule -DisplayName "$RulePrefix*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue
    Write-Host " Adaptive kurallar kaldirildi." -ForegroundColor Green
}

function Show-FirewallStatus {
    $current = Get-CurrentFirewallLevel
    $rules = @(Get-NetFirewallRule -DisplayName "$RulePrefix*" -ErrorAction SilentlyContinue)

    Write-Host ""
    Write-Host " Firewall Durumu:" -ForegroundColor Cyan
    Write-Host " Mod      : $current"
    Write-Host " Kural    : $($rules.Count)"
    Write-Host ""

    if ($rules.Count -gt 0) {
        Write-Host " Aktif kurallar:" -ForegroundColor DarkGray
        foreach ($rule in $rules | Select-Object -First 10) {
            Write-Host "  • $($rule.DisplayName)"
        }
    }
    Write-Host ""
}
