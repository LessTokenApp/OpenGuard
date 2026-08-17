"""Tests for settings dialog UI component."""

import pytest
from PyQt6.QtWidgets import QDialog

from src.models.settings import Settings
from src.ui.settings_dialog import SettingsDialog


class TestSettingsDialogCreation:
    """Test SettingsDialog instantiation and basic properties."""

    def test_settings_dialog_creation(self, qapp):
        """Test dialog opens without error.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        assert dialog is not None
        assert isinstance(dialog, QDialog)

    def test_settings_dialog_has_tabs(self, qapp):
        """Test that dialog has tab widget.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        assert hasattr(dialog, "tabs")
        assert dialog.tabs is not None

    def test_settings_dialog_has_buttons(self, qapp):
        """Test that dialog has save and cancel buttons.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        assert hasattr(dialog, "save_button")
        assert hasattr(dialog, "cancel_button")
        assert dialog.save_button is not None
        assert dialog.cancel_button is not None


class TestSettingsRetrieval:
    """Test settings retrieval functionality."""

    def test_get_settings_returns_settings_object(self, qapp):
        """Test that dialog returns Settings dataclass.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        settings = dialog.get_settings()
        assert isinstance(settings, Settings)

    def test_settings_default_firewall_level(self, qapp):
        """Test that default firewall level is valid.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        settings = dialog.get_settings()
        assert settings.firewall_level in ["Basic", "Moderate", "Relaxed"]

    def test_settings_default_dns_provider(self, qapp):
        """Test that default DNS provider is set.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        settings = dialog.get_settings()
        assert settings.dns_provider in ["Cloudflare", "Google", "Quad9", "OpenDNS"]

    def test_settings_default_auto_start(self, qapp):
        """Test that default auto_start is set.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        settings = dialog.get_settings()
        assert isinstance(settings.auto_start, bool)


class TestSettingsPersistence:
    """Test that settings can be updated and retrieved."""

    def test_settings_persistence_firewall_level(self, qapp):
        """Test that firewall level can be updated and retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.set_firewall_level("Basic")
        settings = dialog.get_settings()
        assert settings.firewall_level == "Basic"

    def test_settings_persistence_firewall_level_moderate(self, qapp):
        """Test that firewall level can be set to Moderate.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.set_firewall_level("Moderate")
        settings = dialog.get_settings()
        assert settings.firewall_level == "Moderate"

    def test_settings_persistence_firewall_level_relaxed(self, qapp):
        """Test that firewall level can be set to Relaxed.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.set_firewall_level("Relaxed")
        settings = dialog.get_settings()
        assert settings.firewall_level == "Relaxed"

    def test_settings_persistence_dns_provider(self, qapp):
        """Test that DNS provider can be updated and retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.dns_combo.setCurrentText("Google")
        settings = dialog.get_settings()
        assert settings.dns_provider == "Google"

    def test_settings_persistence_auto_start(self, qapp):
        """Test that auto_start setting can be updated and retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.auto_start_check.setChecked(False)
        settings = dialog.get_settings()
        assert settings.auto_start is False

    def test_settings_persistence_dns_enabled(self, qapp):
        """Test that DNS enabled setting can be retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.dns_enabled_check.setChecked(False)
        settings = dialog.get_settings()
        assert settings.dns_enabled is False

    def test_settings_persistence_network_monitoring(self, qapp):
        """Test that network monitoring setting can be retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.network_monitoring_check.setChecked(False)
        settings = dialog.get_settings()
        assert settings.network_monitoring is False

    def test_settings_persistence_dark_mode(self, qapp):
        """Test that dark mode setting can be retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.dark_mode_check.setChecked(False)
        settings = dialog.get_settings()
        assert settings.dark_mode is False

    def test_settings_persistence_systray_enabled(self, qapp):
        """Test that systray enabled setting can be retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.systray_check.setChecked(False)
        settings = dialog.get_settings()
        assert settings.systray_enabled is False

    def test_settings_persistence_analytics_enabled(self, qapp):
        """Test that analytics enabled setting can be retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.analytics_enabled_check.setChecked(False)
        settings = dialog.get_settings()
        assert settings.analytics_enabled is False

    def test_settings_persistence_retention_days(self, qapp):
        """Test that retention days setting can be retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.retention_spin.setValue(30)
        settings = dialog.get_settings()
        assert settings.retention_days == 30

    def test_settings_persistence_show_daily_tips(self, qapp):
        """Test that show daily tips setting can be retrieved.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        dialog.tips_check.setChecked(False)
        settings = dialog.get_settings()
        assert settings.show_daily_tips is False


class TestInitialSettings:
    """Test initialization with initial settings."""

    def test_initialize_with_custom_settings(self, qapp):
        """Test dialog can be initialized with custom settings.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        initial_settings = Settings(
            firewall_level="Relaxed",
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
        dialog = SettingsDialog(initial_settings)
        settings = dialog.get_settings()
        assert settings.firewall_level == "Relaxed"
        assert settings.dns_provider == "Google"
        assert settings.retention_days == 30


class TestSettingsDialogTabPageTheming:
    """Test that the tab page bodies are wired up to actually receive theming.

    Task 20 wired dark_mode into SettingsDialog's own stylesheet, but the
    QWidget instances returned by _create_*_tab() and added via
    self.tabs.addTab() don't inherit a painted background from that
    stylesheet unless they carry a selector-matching objectName (a plain
    QWidget needs an explicit rule to paint stylesheet backgrounds at all).
    """

    def test_all_tab_pages_have_tabpage_object_name(self, qapp):
        """Every tab page widget must expose the objectName the CSS rule targets.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        for index in range(dialog.tabs.count()):
            page = dialog.tabs.widget(index)
            assert page.objectName() == "tabPage", (
                f"tab page at index {index} has objectName "
                f"{page.objectName()!r}, expected 'tabPage'"
            )


class TestSettingsDialogSignals:
    """Test signal emissions from settings dialog."""

    def test_save_button_emits_settings_changed_signal(self, qapp, qtbot):
        """Test that save button emits settings_changed signal.

        Args:
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt robot fixture
        """
        dialog = SettingsDialog()

        with qtbot.waitSignal(dialog.settings_changed, timeout=1000):
            dialog.save_button.click()
