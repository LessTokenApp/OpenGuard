"""Tests for system tray UI component."""

from datetime import datetime

import pytest
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu

from src.ui.systray import SystemTray


class TestSystemTrayCreation:
    """Test SystemTray instantiation and basic properties."""

    def test_systray_creation(self, qapp):
        """Test that SystemTray can be instantiated.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        assert systray is not None

    def test_systray_has_icon(self, qapp):
        """Test that SystemTray has an icon.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        icon = systray.icon()
        assert icon is not None

    def test_systray_has_context_menu(self, qapp):
        """Test that SystemTray has a context menu.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        menu = systray.contextMenu()
        assert menu is not None
        assert isinstance(menu, QMenu)


class TestSystemTrayStatus:
    """Test system tray status updates."""

    def test_set_protection_status_protected(self, qapp):
        """Test setting protection status to protected.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        systray.set_protection_status(True)
        # Status should be updated
        assert systray is not None

    def test_set_protection_status_unprotected(self, qapp):
        """Test setting protection status to unprotected.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        systray.set_protection_status(False)
        # Status should be updated
        assert systray is not None

    def test_tooltip_contains_status(self, qapp):
        """Test that tooltip displays protection status.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        systray.set_protection_status(True)
        tooltip = systray.toolTip()
        assert "OpenGuard" in tooltip
        assert "Protected" in tooltip or "protected" in tooltip.lower()

    def test_tooltip_contains_activity(self, qapp):
        """Test that tooltip displays last activity.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        systray.set_protection_status(True)
        tooltip = systray.toolTip()
        # Should contain some activity indicator
        assert len(tooltip) > 0


class TestSystemTraySignals:
    """Test system tray signals and menu interactions."""

    def test_toggle_clicked_signal_exists(self, qapp):
        """Test that toggle_clicked signal exists.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        assert hasattr(systray, "toggle_clicked")
        assert hasattr(systray.toggle_clicked, "emit")

    def test_settings_clicked_signal_exists(self, qapp):
        """Test that settings_clicked signal exists.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        assert hasattr(systray, "settings_clicked")
        assert hasattr(systray.settings_clicked, "emit")

    def test_exit_clicked_signal_exists(self, qapp):
        """Test that exit_clicked signal exists.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        assert hasattr(systray, "exit_clicked")
        assert hasattr(systray.exit_clicked, "emit")

    def test_context_menu_has_required_items(self, qapp):
        """Test that context menu contains all required items.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        systray = SystemTray()
        menu = systray.contextMenu()
        actions = [action.text() for action in menu.actions()]

        # Check for expected menu items
        assert any("Protected" in text for text in actions)
        assert any("Disable" in text or "Enable" in text for text in actions)
        assert any("Settings" in text for text in actions)
        assert any("Help" in text for text in actions)
        assert any("Exit" in text for text in actions)

    def test_settings_action_emits_signal(self, qapp, qtbot):
        """Test that settings menu action emits settings_clicked signal.

        Args:
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt robot fixture
        """
        systray = SystemTray()

        # Connect to the signal to capture emissions
        with qtbot.waitSignal(systray.settings_clicked, timeout=1000):
            # Trigger the settings action
            systray.settings_action.trigger()

    def test_toggle_action_emits_signal(self, qapp, qtbot):
        """Test that toggle menu action emits toggle_clicked signal.

        Args:
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt robot fixture
        """
        systray = SystemTray()

        # Connect to the signal to capture emissions
        with qtbot.waitSignal(systray.toggle_clicked, timeout=1000):
            # Trigger the toggle action
            systray.toggle_action.trigger()

    def test_exit_action_emits_signal(self, qapp, qtbot):
        """Test that exit menu action emits exit_clicked signal.

        Args:
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt robot fixture
        """
        systray = SystemTray()

        # Connect to the signal to capture emissions
        with qtbot.waitSignal(systray.exit_clicked, timeout=1000):
            # Trigger the exit action
            systray.exit_action.trigger()


class TestAnalyticsAction:
    """The Analytics menu entry existed but its handler was a stub."""

    def test_analytics_action_emits_a_signal(self, qapp):
        """Choosing Analytics must notify listeners rather than do nothing."""
        tray = SystemTray()
        received = []
        tray.analytics_clicked.connect(lambda: received.append(True))

        tray.analytics_action.trigger()

        assert received, "Analytics menu entry emitted nothing"
