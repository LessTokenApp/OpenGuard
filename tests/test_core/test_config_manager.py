"""Tests for ConfigManager core module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.config_manager import ConfigManager
from src.models.settings import Settings


@pytest.fixture
def temp_config_dir():
    """Provide a temporary directory for config files.

    Yields:
        Path: Temporary directory path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_file(temp_config_dir):
    """Provide a temporary config file path.

    Args:
        temp_config_dir: Temporary directory fixture

    Yields:
        Path: Path to temporary config file
    """
    config_file = temp_config_dir / "config.yaml"
    yield config_file


class TestConfigManagerInstantiation:
    """Test ConfigManager creation and initialization."""

    def test_config_manager_creation(self):
        """Test ConfigManager can be instantiated."""
        manager = ConfigManager()
        assert manager is not None

    def test_config_manager_with_custom_path(self, temp_config_file):
        """Test ConfigManager can be instantiated with custom config path.

        Args:
            temp_config_file: Temporary config file path
        """
        manager = ConfigManager(config_path=temp_config_file)
        assert manager is not None
        assert manager.config_path == temp_config_file

    def test_default_config_path_uses_home_directory(self):
        """Test default config path is ~/.openguard/config.yaml."""
        manager = ConfigManager()
        expected_path = Path.home() / ".openguard" / "config.yaml"
        assert manager.config_path == expected_path


class TestLoadConfig:
    """Test load_config method."""

    def test_load_config_returns_settings(self, temp_config_dir):
        """Test load_config returns Settings instance.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        # Create a minimal config file
        config_file.write_text(
            """
firewall_level: Basic
dns_provider: Google
dns_enabled: false
network_monitoring: true
auto_start: false
dark_mode: false
systray_enabled: true
analytics_enabled: false
retention_days: 30
show_daily_tips: false
"""
        )

        manager = ConfigManager(config_path=config_file)
        settings = manager.load_config()

        assert isinstance(settings, Settings)
        assert settings.firewall_level == "Basic"
        assert settings.dns_provider == "Google"
        assert settings.dns_enabled is False
        assert settings.network_monitoring is True

    def test_load_config_returns_defaults_when_file_missing(self, temp_config_dir):
        """Test load_config returns default settings when file is missing.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        assert not config_file.exists()

        manager = ConfigManager(config_path=config_file)
        settings = manager.load_config()

        assert isinstance(settings, Settings)
        # Verify defaults from Settings dataclass
        assert settings.firewall_level == "Moderate"
        assert settings.dns_provider == "Cloudflare"
        assert settings.dns_enabled is True
        assert settings.network_monitoring is True
        assert settings.auto_start is True
        assert settings.dark_mode is True
        assert settings.systray_enabled is True
        assert settings.analytics_enabled is True
        assert settings.retention_days == 90
        assert settings.show_daily_tips is True

    def test_load_config_with_partial_config_file(self, temp_config_dir):
        """Test load_config handles partial config files with defaults.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        # Create a partial config file (only some fields)
        config_file.write_text(
            """
firewall_level: Relaxed
dns_enabled: false
"""
        )

        manager = ConfigManager(config_path=config_file)
        settings = manager.load_config()

        assert settings.firewall_level == "Relaxed"
        assert settings.dns_enabled is False
        # Other fields should have defaults
        assert settings.dns_provider == "Cloudflare"
        assert settings.auto_start is True

    def test_load_config_handles_invalid_yaml(self, temp_config_dir):
        """Test load_config handles invalid YAML gracefully.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        # Create an invalid YAML file
        config_file.write_text("invalid: yaml: content: [")

        manager = ConfigManager(config_path=config_file)
        settings = manager.load_config()

        # Should fall back to defaults
        assert isinstance(settings, Settings)
        assert settings.firewall_level == "Moderate"

    def test_load_config_handles_invalid_settings_values(self, temp_config_dir):
        """Test load_config handles invalid settings values.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        # Create a config with invalid firewall level
        config_file.write_text(
            """
firewall_level: InvalidLevel
dns_provider: Google
"""
        )

        manager = ConfigManager(config_path=config_file)
        settings = manager.load_config()

        # Should fall back to defaults due to validation error
        assert isinstance(settings, Settings)
        assert settings.firewall_level == "Moderate"

    def test_load_config_type_conversion(self, temp_config_dir):
        """Test load_config correctly converts YAML types.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text(
            """
firewall_level: Basic
dns_enabled: true
retention_days: 60
analytics_enabled: false
"""
        )

        manager = ConfigManager(config_path=config_file)
        settings = manager.load_config()

        assert isinstance(settings.dns_enabled, bool)
        assert isinstance(settings.retention_days, int)
        assert isinstance(settings.analytics_enabled, bool)


class TestSaveConfig:
    """Test save_config method."""

    def test_save_config_creates_file(self, temp_config_dir):
        """Test save_config creates config file.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        manager = ConfigManager(config_path=config_file)

        settings = Settings(firewall_level="Basic", dns_provider="Google")
        result = manager.save_config(settings)

        assert result is True
        assert config_file.exists()

    def test_save_config_writes_correct_data(self, temp_config_dir):
        """Test save_config writes correct data to file.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        manager = ConfigManager(config_path=config_file)

        settings = Settings(
            firewall_level="Relaxed",
            dns_provider="Quad9",
            dns_enabled=False,
            retention_days=45,
        )
        manager.save_config(settings)

        # Read and verify
        loaded_settings = manager.load_config()
        assert loaded_settings.firewall_level == "Relaxed"
        assert loaded_settings.dns_provider == "Quad9"
        assert loaded_settings.dns_enabled is False
        assert loaded_settings.retention_days == 45

    def test_save_config_creates_directory_if_missing(self, temp_config_dir):
        """Test save_config creates config directory if it doesn't exist.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "subdir" / "config.yaml"
        assert not config_file.parent.exists()

        manager = ConfigManager(config_path=config_file)
        settings = Settings()
        result = manager.save_config(settings)

        assert result is True
        assert config_file.exists()

    def test_save_config_overwrites_existing_file(self, temp_config_dir):
        """Test save_config overwrites existing config file.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        manager = ConfigManager(config_path=config_file)

        # Write first config
        settings1 = Settings(firewall_level="Basic")
        manager.save_config(settings1)

        # Write second config
        settings2 = Settings(firewall_level="Relaxed")
        result = manager.save_config(settings2)

        assert result is True
        loaded = manager.load_config()
        assert loaded.firewall_level == "Relaxed"

    def test_save_config_returns_false_on_error(self, temp_config_dir):
        """Test save_config returns False on write error.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        manager = ConfigManager(config_path=config_file)

        settings = Settings()

        # Mock file operation to raise an exception
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = manager.save_config(settings)

        assert result is False

    def test_save_config_all_fields(self, temp_config_dir):
        """Test save_config saves all Settings fields correctly.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        manager = ConfigManager(config_path=config_file)

        settings = Settings(
            firewall_level="Basic",
            dns_provider="Google",
            dns_enabled=False,
            network_monitoring=False,
            auto_start=False,
            dark_mode=False,
            systray_enabled=False,
            analytics_enabled=False,
            retention_days=30,
            show_daily_tips=False,
        )
        manager.save_config(settings)

        loaded = manager.load_config()
        assert loaded.firewall_level == "Basic"
        assert loaded.dns_provider == "Google"
        assert loaded.dns_enabled is False
        assert loaded.network_monitoring is False
        assert loaded.auto_start is False
        assert loaded.dark_mode is False
        assert loaded.systray_enabled is False
        assert loaded.analytics_enabled is False
        assert loaded.retention_days == 30
        assert loaded.show_daily_tips is False


class TestConfigRoundTrip:
    """Test save and load round-trip consistency."""

    def test_save_and_load_round_trip(self, temp_config_dir):
        """Test saving and loading preserves all settings.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        config_file = temp_config_dir / "config.yaml"
        manager = ConfigManager(config_path=config_file)

        original = Settings(
            firewall_level="Relaxed",
            dns_provider="Quad9",
            dns_enabled=False,
            network_monitoring=True,
            auto_start=False,
            dark_mode=True,
            systray_enabled=False,
            analytics_enabled=True,
            retention_days=60,
            show_daily_tips=False,
        )

        manager.save_config(original)
        loaded = manager.load_config()

        assert loaded.firewall_level == original.firewall_level
        assert loaded.dns_provider == original.dns_provider
        assert loaded.dns_enabled == original.dns_enabled
        assert loaded.network_monitoring == original.network_monitoring
        assert loaded.auto_start == original.auto_start
        assert loaded.dark_mode == original.dark_mode
        assert loaded.systray_enabled == original.systray_enabled
        assert loaded.analytics_enabled == original.analytics_enabled
        assert loaded.retention_days == original.retention_days
        assert loaded.show_daily_tips == original.show_daily_tips


class TestConfigPathHandling:
    """Test cross-platform path handling."""

    def test_config_path_cross_platform_home(self):
        """Test config path uses pathlib for cross-platform compatibility."""
        manager = ConfigManager()
        assert isinstance(manager.config_path, Path)
        assert ".openguard" in str(manager.config_path)
        assert "config.yaml" in str(manager.config_path)

    def test_config_path_custom_absolute_path(self, temp_config_file):
        """Test custom absolute path works correctly.

        Args:
            temp_config_file: Temporary config file path
        """
        manager = ConfigManager(config_path=temp_config_file)
        assert manager.config_path.is_absolute()
        assert manager.config_path == temp_config_file

    def test_load_creates_missing_parent_directories(self, temp_config_dir):
        """Test load_config handles missing parent directories.

        Args:
            temp_config_dir: Temporary directory fixture
        """
        deep_config_path = temp_config_dir / "a" / "b" / "c" / "config.yaml"
        manager = ConfigManager(config_path=deep_config_path)

        # Should not raise exception, just return defaults
        settings = manager.load_config()
        assert isinstance(settings, Settings)
