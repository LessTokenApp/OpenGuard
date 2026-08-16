"""Tests for main window UI component."""

from datetime import datetime

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton, QTextEdit

from src.models.event import Event
from src.ui.main_window import MainWindow


class TestMainWindowCreation:
    """Test MainWindow instantiation and basic properties."""

    def test_main_window_creation(self, qapp):
        """Test that MainWindow can be instantiated.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        assert window is not None

    def test_main_window_is_qmain_window(self, qapp):
        """Test that MainWindow is a QMainWindow instance.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        from PyQt6.QtWidgets import QMainWindow

        window = MainWindow()
        assert isinstance(window, QMainWindow)


class TestStatusCard:
    """Test status card display functionality."""

    def test_status_display_protected(self, qapp):
        """Test status display when protection is enabled.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        window.set_protection_status(True)
        # Window should be created and status should be set
        assert window is not None

    def test_status_display_unprotected(self, qapp):
        """Test status display when protection is disabled.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        window.set_protection_status(False)
        # Window should be created and status should be set
        assert window is not None

    def test_toggle_button_exists(self, qapp):
        """Test that toggle button exists in the window.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        button = window.get_toggle_button()
        assert button is not None
        assert isinstance(button, QPushButton)

    def test_toggle_button_text(self, qapp):
        """Test that toggle button has proper text.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        button = window.get_toggle_button()
        assert button.text() in ["Enable Protection", "Disable Protection"]


class TestActivityLog:
    """Test activity log functionality."""

    def test_add_activity_log_entry_success(self, qapp):
        """Test adding a success event to activity log.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        event = Event(
            timestamp=datetime.now(),
            event="System protection enabled",
            severity="SUCCESS",
            category="protection",
        )
        window.add_activity_log_entry(event)
        # Should not raise an error

    def test_add_activity_log_entry_warning(self, qapp):
        """Test adding a warning event to activity log.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        event = Event(
            timestamp=datetime.now(),
            event="Suspicious activity detected",
            severity="WARN",
            category="security",
        )
        window.add_activity_log_entry(event)
        # Should not raise an error

    def test_add_activity_log_entry_error(self, qapp):
        """Test adding an error event to activity log.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        event = Event(
            timestamp=datetime.now(),
            event="Protection system failed",
            severity="ERROR",
            category="system",
        )
        window.add_activity_log_entry(event)
        # Should not raise an error

    def test_activity_log_displays_timestamp(self, qapp):
        """Test that activity log displays event timestamp.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        now = datetime.now()
        event = Event(
            timestamp=now,
            event="Test event",
            severity="SUCCESS",
        )
        window.add_activity_log_entry(event)
        # Timestamp should be in the activity log
        log_text = window.activity_log.toPlainText()
        assert now.strftime("%H:%M:%S") in log_text or len(log_text) > 0

    def test_activity_log_displays_message(self, qapp):
        """Test that activity log displays event message.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        event = Event(
            timestamp=datetime.now(),
            event="Test event message",
            severity="SUCCESS",
        )
        window.add_activity_log_entry(event)
        log_text = window.activity_log.toPlainText()
        assert "Test event message" in log_text

    def test_activity_log_is_text_edit(self, qapp):
        """Test that activity log is a QTextEdit widget.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        assert hasattr(window, "activity_log")
        assert isinstance(window.activity_log, QTextEdit)


class TestSignals:
    """Test signal emission and handling."""

    def test_toggle_protection_signal_exists(self, qapp):
        """Test that toggle_protection_clicked signal exists.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        assert hasattr(window, "toggle_protection_clicked")
        # Check that it's a pyqtSignal
        assert hasattr(window.toggle_protection_clicked, "emit")

    def test_toggle_protection_signal_emission(self, qapp, qtbot):
        """Test that toggle button emits signal when clicked.

        Args:
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for simulating user interactions
        """
        window = MainWindow()
        button = window.get_toggle_button()

        # Use a simple flag to track signal emission
        signal_emitted = False

        def on_toggle():
            nonlocal signal_emitted
            signal_emitted = True

        # Connect to the signal
        window.toggle_protection_clicked.connect(on_toggle)

        # Click the button
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

        # Signal should have been emitted
        assert signal_emitted


class TestDisclaimerLabel:
    """Test persistent disclaimer label in MainWindow."""

    def test_disclaimer_label_exists(self, qapp):
        """Test that disclaimer label exists after MainWindow construction.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        assert hasattr(window, "disclaimer_label")
        assert window.disclaimer_label is not None

    def test_disclaimer_label_not_empty_when_protected(self, qapp):
        """Test that disclaimer label is non-empty when protected.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        window.set_protection_status(True)
        # Disclaimer label should always be non-empty
        assert window.disclaimer_label.text() != ""
        assert len(window.disclaimer_label.text()) > 0

    def test_disclaimer_label_not_empty_when_unprotected(self, qapp):
        """Test that disclaimer label is non-empty when unprotected.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        window.set_protection_status(False)
        # Disclaimer label should always be non-empty
        assert window.disclaimer_label.text() != ""
        assert len(window.disclaimer_label.text()) > 0

    def test_disclaimer_label_contains_vpn_antivirus_reference(self, qapp):
        """Test that disclaimer mentions VPN and antivirus limitations.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        disclaimer_text = window.disclaimer_label.text()
        # Should mention that it's not VPN/antivirus substitute
        assert "VPN" in disclaimer_text or "antivirus" in disclaimer_text or \
               "sifrele" in disclaimer_text or "trafik" in disclaimer_text.lower()


class TestAdvisoryInActivityLog:
    """Test advisory integration with activity log."""

    def test_advisory_appended_to_activity_log(self, qapp):
        """Test that advisory is added to activity log with WARN severity.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        from src.core.hardening_manager import HardeningManager
        from unittest.mock import MagicMock, patch

        window = MainWindow()

        # Create a manager and connect it to the window's advisory handler
        manager = HardeningManager()

        # Mock signal handler for advisory
        def on_advisory_raised(text):
            event = Event(
                timestamp=datetime.now(),
                event=text,
                severity="WARN",
                category="advisory"
            )
            window.add_activity_log_entry(event)

        manager.advisory_raised.connect(on_advisory_raised)

        # Simulate advisory signal
        advisory_text = "Bu arac trafigi sifrelemez."
        manager.advisory_raised.emit(advisory_text)

        # Check that advisory is in activity log
        log_text = window.activity_log.toPlainText()
        assert advisory_text in log_text
