"""ConfigManager for handling YAML configuration I/O."""

from pathlib import Path
from typing import Optional

import yaml

from src.models.settings import Settings


class ConfigManager:
    """Manages loading and saving configuration from/to YAML files.

    This class provides cross-platform configuration management using pathlib
    for path handling. It handles YAML serialization/deserialization of Settings
    objects and provides sensible defaults when configuration files are missing.

    Attributes:
        config_path (Path): Path to the YAML configuration file
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize ConfigManager with optional custom config path.

        Args:
            config_path: Optional custom path to config.yaml file.
                        Defaults to ~/.openguard/config.yaml
        """
        if config_path is None:
            self.config_path = Path.home() / ".openguard" / "config.yaml"
        else:
            self.config_path = config_path

    def load_config(self) -> Settings:
        """Load configuration from YAML file.

        Returns default Settings if file doesn't exist or contains invalid data.
        Handles missing files, invalid YAML, and invalid field values gracefully.

        Returns:
            Settings: Loaded settings or defaults if file is missing/invalid
        """
        # If file doesn't exist, return defaults
        if not self.config_path.exists():
            return Settings()

        try:
            # Read and parse YAML file
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Handle empty or invalid YAML
            if data is None:
                return Settings()

            if not isinstance(data, dict):
                return Settings()

            # Create Settings from loaded data, allowing defaults for missing fields
            return Settings(**data)

        except yaml.YAMLError:
            # Invalid YAML syntax - return defaults
            return Settings()
        except ValueError:
            # Invalid settings values (e.g., invalid firewall_level)
            return Settings()
        except (IOError, OSError):
            # File read error - return defaults
            return Settings()
        except TypeError:
            # Invalid type for Settings initialization - return defaults
            return Settings()

    def save_config(self, settings: Settings) -> bool:
        """Save configuration to YAML file.

        Creates parent directories if they don't exist. Overwrites existing
        configuration files.

        Args:
            settings: Settings object to save

        Returns:
            bool: True if save succeeded, False otherwise
        """
        try:
            # Create parent directories if they don't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert Settings to dictionary
            data = {
                "firewall_level": settings.firewall_level,
                "dns_provider": settings.dns_provider,
                "dns_enabled": settings.dns_enabled,
                "network_monitoring": settings.network_monitoring,
                "auto_start": settings.auto_start,
                "dark_mode": settings.dark_mode,
                "systray_enabled": settings.systray_enabled,
                "analytics_enabled": settings.analytics_enabled,
                "retention_days": settings.retention_days,
                "show_daily_tips": settings.show_daily_tips,
            }

            # Write to YAML file
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            return True

        except (IOError, OSError):
            # File write error
            return False
        except Exception:
            # Unexpected error
            return False
