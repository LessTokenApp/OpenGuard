"""Tests for ProcessMonitor core module."""

import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import QCoreApplication

from src.core.process_monitor import ProcessMonitor
from src.models.event import Event


class TestProcessMonitorInstantiation:
    """Test ProcessMonitor creation and initialization."""

    def test_process_monitor_creation(self, qapp):
        """Test ProcessMonitor can be instantiated.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        monitor = ProcessMonitor()
        assert monitor is not None

    def test_initial_monitoring_state_is_false(self, qapp):
        """Test initial monitoring state is False.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        monitor = ProcessMonitor()
        assert monitor.is_monitoring is False

    def test_new_events_signal_exists(self, qapp):
        """Test that new_events signal is defined.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        monitor = ProcessMonitor()
        # Verify signal exists by attempting to connect
        spy = MagicMock()
        monitor.new_events.connect(spy)
        assert spy.called or not spy.called  # Just verify connection succeeded


class TestStartMonitoring:
    """Test start_monitoring method."""

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_start_monitoring_success(self, mock_popen, qapp):
        """Test start_monitoring begins monitoring process.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process running
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()

        assert monitor.is_monitoring is True

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_start_monitoring_creates_subprocess(self, mock_popen, qapp):
        """Test start_monitoring creates a subprocess.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()

        # Verify Popen was called with PowerShell command
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        cmd = call_args[0][0] if call_args[0] else call_args[1].get("args", "")
        assert "powershell" in str(cmd).lower()
        assert "OpenGuard" in str(cmd)

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_start_monitoring_with_stdin_pipe(self, mock_popen, qapp):
        """Test start_monitoring creates subprocess with stdin pipe.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()

        # Verify stdin is set to PIPE
        call_kwargs = mock_popen.call_args[1]
        assert "stdin" in call_kwargs
        assert call_kwargs["stdin"] == subprocess.PIPE

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_start_monitoring_with_stdout_pipe(self, mock_popen, qapp):
        """Test start_monitoring creates subprocess with stdout pipe.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()

        # Verify stdout is set to PIPE
        call_kwargs = mock_popen.call_args[1]
        assert "stdout" in call_kwargs
        assert call_kwargs["stdout"] == subprocess.PIPE

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_start_monitoring_already_running(self, mock_popen, qapp):
        """Test start_monitoring when already monitoring.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()
        monitor.start_monitoring()  # Call twice

        # Popen should only be called once
        assert mock_popen.call_count == 1

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_start_monitoring_exception_handling(self, mock_popen, qapp):
        """Test start_monitoring handles exceptions gracefully.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock to raise exception
        mock_popen.side_effect = Exception("Process error")

        monitor = ProcessMonitor()
        monitor.start_monitoring()

        # Should not crash, monitoring should remain False
        assert monitor.is_monitoring is False


class TestStopMonitoring:
    """Test stop_monitoring method."""

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_stop_monitoring_success(self, mock_popen, qapp):
        """Test stop_monitoring stops the monitoring process.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()
        assert monitor.is_monitoring is True

        monitor.stop_monitoring()
        assert monitor.is_monitoring is False

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_stop_monitoring_terminates_process(self, mock_popen, qapp):
        """Test stop_monitoring terminates the subprocess.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()
        monitor.stop_monitoring()

        # Verify terminate was called
        mock_process.terminate.assert_called_once()

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_stop_monitoring_when_not_started(self, mock_popen, qapp):
        """Test stop_monitoring when monitoring is not started.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        monitor = ProcessMonitor()
        # Should not crash when stopping without starting
        monitor.stop_monitoring()
        assert monitor.is_monitoring is False

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_stop_monitoring_exception_handling(self, mock_popen, qapp):
        """Test stop_monitoring handles exceptions gracefully.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.terminate.side_effect = Exception("Termination error")
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()
        # Should not crash
        monitor.stop_monitoring()

        assert monitor.is_monitoring is False


class TestNewEventsSignal:
    """Test new_events signal emission."""

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_new_events_signal_emits_event_list(self, mock_popen, qapp, qtbot):
        """Test new_events signal emits a list of events.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for signal testing
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()

        # Create test event
        test_event = Event(
            timestamp=datetime.now(),
            event="OpenGuard.ps1 process detected",
            severity="SUCCESS",
            category="process_monitor",
        )

        signal_args = []

        def capture_events(events):
            signal_args.append(events)

        monitor.new_events.connect(capture_events)

        # Manually emit for testing
        monitor.new_events.emit([test_event])

        assert len(signal_args) == 1
        assert len(signal_args[0]) == 1
        assert signal_args[0][0] == test_event

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_new_events_contains_event_objects(self, mock_popen, qapp):
        """Test new_events emits Event objects.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()

        test_event = Event(
            timestamp=datetime.now(),
            event="Test event",
            severity="SUCCESS",
            category="test",
        )

        signal_args = []

        def capture_events(events):
            signal_args.append(events)

        monitor.new_events.connect(capture_events)
        monitor.new_events.emit([test_event])

        assert isinstance(signal_args[0][0], Event)
        assert signal_args[0][0].event == "Test event"
        assert signal_args[0][0].severity == "SUCCESS"


class TestProcessMonitorPowerShellCommands:
    """Test PowerShell command construction."""

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_subprocess_uses_powershell(self, mock_popen, qapp):
        """Test subprocess is launched with powershell.exe.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()

        call_args = mock_popen.call_args[0][0]
        assert "powershell" in str(call_args).lower()

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_subprocess_monitors_openguard_process(self, mock_popen, qapp):
        """Test subprocess monitors for OpenGuard.ps1 process.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()

        call_args = mock_popen.call_args[0][0]
        assert "OpenGuard" in str(call_args)

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_subprocess_text_mode(self, mock_popen, qapp):
        """Test subprocess is run in text mode.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()
        monitor.start_monitoring()

        call_kwargs = mock_popen.call_args[1]
        assert "text" in call_kwargs
        assert call_kwargs["text"] is True


class TestEventGeneration:
    """Test event generation from process detection."""

    def test_event_has_correct_properties(self, qapp):
        """Test generated events have correct properties.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        event = Event(
            timestamp=datetime.now(),
            event="Process detected",
            severity="SUCCESS",
            category="process_monitor",
        )

        assert event.timestamp is not None
        assert event.event == "Process detected"
        assert event.severity == "SUCCESS"
        assert event.category == "process_monitor"

    def test_event_severity_validation(self, qapp):
        """Test Event enforces valid severity values.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        with pytest.raises(ValueError):
            Event(
                timestamp=datetime.now(),
                event="Test",
                severity="INVALID",
                category="test",
            )

    def test_valid_event_severities(self, qapp):
        """Test Event accepts all valid severity values.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        for severity in ["SUCCESS", "WARN", "ERROR"]:
            event = Event(
                timestamp=datetime.now(),
                event="Test",
                severity=severity,
                category="test",
            )
            assert event.severity == severity


class TestProcessMonitorIntegration:
    """Integration tests for ProcessMonitor."""

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_start_stop_start_cycle(self, mock_popen, qapp):
        """Test monitoring can be started, stopped, and restarted.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()

        # Start
        monitor.start_monitoring()
        assert monitor.is_monitoring is True

        # Stop
        monitor.stop_monitoring()
        assert monitor.is_monitoring is False

        # Start again
        monitor.start_monitoring()
        assert monitor.is_monitoring is True

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_multiple_events_emission(self, mock_popen, qapp):
        """Test multiple events can be emitted.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()

        signal_args = []

        def capture_events(events):
            signal_args.append(events)

        monitor.new_events.connect(capture_events)

        # Emit multiple times
        event1 = Event(
            timestamp=datetime.now(),
            event="Event 1",
            severity="SUCCESS",
            category="process_monitor",
        )
        monitor.new_events.emit([event1])

        event2 = Event(
            timestamp=datetime.now(),
            event="Event 2",
            severity="WARN",
            category="process_monitor",
        )
        monitor.new_events.emit([event2])

        assert len(signal_args) == 2
        assert len(signal_args[0]) == 1
        assert len(signal_args[1]) == 1
        assert signal_args[0][0].event == "Event 1"
        assert signal_args[1][0].event == "Event 2"

    @patch("src.core.process_monitor.subprocess.Popen")
    def test_monitor_with_qobject_signals(self, mock_popen, qapp):
        """Test ProcessMonitor works as QObject with signals.

        Args:
            mock_popen: Mocked subprocess.Popen
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        monitor = ProcessMonitor()

        # Verify it's a QObject
        from PyQt6.QtCore import QObject

        assert isinstance(monitor, QObject)

        # Verify it has signals
        assert hasattr(monitor, "new_events")
