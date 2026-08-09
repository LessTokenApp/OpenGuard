"""Settings dataclass for user configuration."""

from dataclasses import dataclass


@dataclass
class Settings:
    """User configuration.

    Attributes:
        firewall_level: Level of firewall protection ("Basic", "Moderate", "Relaxed")
        dns_provider: DNS provider to use ("Cloudflare", "Google", "Quad9")
        dns_enabled: Whether DNS security is enabled
        network_monitoring: Whether to monitor gateway MAC
        auto_start: Whether to auto-start on login
        dark_mode: Whether to use dark mode
        systray_enabled: Whether system tray integration is enabled
        analytics_enabled: Whether to auto-log events
        retention_days: Number of days to retain event logs
        show_daily_tips: Whether to show daily tips
    """

    firewall_level: str = "Moderate"  # Basic, Moderate, Relaxed
    dns_provider: str = "Cloudflare"  # Cloudflare, Google, Quad9
    dns_enabled: bool = True
    network_monitoring: bool = True
    auto_start: bool = True
    dark_mode: bool = True
    systray_enabled: bool = True
    analytics_enabled: bool = True
    retention_days: int = 90
    show_daily_tips: bool = True

    def __post_init__(self) -> None:
        """Validate settings after initialization.

        Raises:
            ValueError: If firewall_level is not one of the valid options
        """
        if self.firewall_level not in ["Basic", "Moderate", "Relaxed"]:
            raise ValueError(
                f"Invalid firewall level: {self.firewall_level}. "
                f"Must be one of: Basic, Moderate, Relaxed"
            )
