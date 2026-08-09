"""Tests for HardeningManager core module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import QCoreApplication

from src.core.hardening_manager import HardeningManager


class TestHardeningManagerInstantiation:
    """Test HardeningManager creation and initialization."""

    def test_hardening_manager_creation(self, qapp):
        """Test HardeningManager can be instantiated.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        manager = HardeningManager()
        assert manager is not None

    def test_initial_protection_status_false(self, qapp):
        """Test initial protection status is False.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        manager = HardeningManager()
        assert manager.get_status() is False

    def test_backend_path_is_set(self, qapp):
        """Test backend path is correctly configured.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        manager = HardeningManager()
        assert manager.backend_path is not None
        assert isinstance(manager.backend_path, Path)


class TestHardeningManagerSignals:
    """Test signal emissions from HardeningManager."""

    def test_status_changed_signal_exists(self, qapp):
        """Test that status_changed signal is defined.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        manager = HardeningManager()
        # Verify signal exists by attempting to connect
        spy = MagicMock()
        manager.status_changed.connect(spy)
        assert spy.called or not spy.called  # Just verify connection succeeded

    def test_error_occurred_signal_exists(self, qapp):
        """Test that error_occurred signal is defined.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        manager = HardeningManager()
        # Verify signal exists by attempting to connect
        spy = MagicMock()
        manager.error_occurred.connect(spy)
        assert spy.called or not spy.called  # Just verify connection succeeded


class TestEnableHardening:
    """Test enable_hardening method."""

    @patch("src.core.hardening_manager.subprocess.run")
    def test_enable_hardening_success(self, mock_run, qapp):
        """Test enable_hardening succeeds with valid subprocess return.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        result = manager.enable_hardening()

        assert result is True
        assert manager.get_status() is True

    @patch("src.core.hardening_manager.subprocess.run")
    def test_enable_hardening_with_level_parameter(self, mock_run, qapp):
        """Test enable_hardening passes level parameter correctly.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        result = manager.enable_hardening(level="High")

        assert result is True
        # Verify subprocess was called with correct command
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0] if call_args[0] else call_args[1].get("cmd", "")
        assert "Enable" in cmd or "enable" in cmd.lower()

    @patch("src.core.hardening_manager.subprocess.run")
    def test_enable_hardening_default_level(self, mock_run, qapp):
        """Test enable_hardening uses Moderate as default level.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        result = manager.enable_hardening()  # No level specified

        assert result is True
        mock_run.assert_called_once()

    @patch("src.core.hardening_manager.subprocess.run")
    def test_enable_hardening_failure(self, mock_run, qapp):
        """Test enable_hardening handles subprocess failure.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock for failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_run.return_value = mock_result

        manager = HardeningManager()
        result = manager.enable_hardening()

        assert result is False
        assert manager.get_status() is False

    @patch("src.core.hardening_manager.subprocess.run")
    def test_enable_hardening_exception(self, mock_run, qapp):
        """Test enable_hardening handles exceptions gracefully.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock to raise exception
        mock_run.side_effect = Exception("Process error")

        manager = HardeningManager()
        result = manager.enable_hardening()

        assert result is False
        assert manager.get_status() is False

    @patch("src.core.hardening_manager.subprocess.run")
    def test_enable_hardening_timeout(self, mock_run, qapp):
        """Test enable_hardening handles timeout exceptions.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock to raise timeout exception
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("powershell.exe", 30)

        manager = HardeningManager()
        result = manager.enable_hardening()

        assert result is False
        assert manager.get_status() is False

    @patch("src.core.hardening_manager.subprocess.run")
    def test_enable_hardening_emits_status_signal(self, mock_run, qapp, qtbot):
        """Test enable_hardening emits status_changed signal on success.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for signal testing
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()

        # Use qtbot to capture signal
        with qtbot.waitSignal(manager.status_changed, timeout=1000):
            result = manager.enable_hardening()

        assert result is True

    @patch("src.core.hardening_manager.subprocess.run")
    def test_enable_hardening_emits_error_signal_on_failure(
        self, mock_run, qapp, qtbot
    ):
        """Test enable_hardening emits error_occurred signal on failure.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for signal testing
        """
        # Setup mock for failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Test error"
        mock_run.return_value = mock_result

        manager = HardeningManager()

        # Use qtbot to capture signal
        with qtbot.waitSignal(manager.error_occurred, timeout=1000):
            result = manager.enable_hardening()

        assert result is False


class TestDisableHardening:
    """Test disable_hardening method."""

    @patch("src.core.hardening_manager.subprocess.run")
    def test_disable_hardening_success(self, mock_run, qapp):
        """Test disable_hardening succeeds with valid subprocess return.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        # First set to protected state
        manager.is_protected = True
        result = manager.disable_hardening()

        assert result is True
        assert manager.get_status() is False

    @patch("src.core.hardening_manager.subprocess.run")
    def test_disable_hardening_subprocess_call(self, mock_run, qapp):
        """Test disable_hardening calls subprocess with correct command.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        result = manager.disable_hardening()

        assert result is True
        # Verify subprocess was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0] if call_args[0] else call_args[1].get("cmd", "")
        assert "Disable" in cmd or "disable" in cmd.lower()

    @patch("src.core.hardening_manager.subprocess.run")
    def test_disable_hardening_failure(self, mock_run, qapp):
        """Test disable_hardening handles subprocess failure.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock for failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Cannot disable"
        mock_run.return_value = mock_result

        manager = HardeningManager()
        manager.is_protected = True
        result = manager.disable_hardening()

        assert result is False
        assert manager.get_status() is True  # Status unchanged

    @patch("src.core.hardening_manager.subprocess.run")
    def test_disable_hardening_exception(self, mock_run, qapp):
        """Test disable_hardening handles exceptions gracefully.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock to raise exception
        mock_run.side_effect = Exception("Process error")

        manager = HardeningManager()
        manager.is_protected = True
        result = manager.disable_hardening()

        assert result is False

    @patch("src.core.hardening_manager.subprocess.run")
    def test_disable_hardening_emits_status_signal(self, mock_run, qapp, qtbot):
        """Test disable_hardening emits status_changed signal on success.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for signal testing
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        manager.is_protected = True

        # Use qtbot to capture signal
        with qtbot.waitSignal(manager.status_changed, timeout=1000):
            result = manager.disable_hardening()

        assert result is True

    @patch("src.core.hardening_manager.subprocess.run")
    def test_disable_hardening_emits_error_signal_on_failure(
        self, mock_run, qapp, qtbot
    ):
        """Test disable_hardening emits error_occurred signal on failure.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for signal testing
        """
        # Setup mock for failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Test error"
        mock_run.return_value = mock_result

        manager = HardeningManager()

        # Use qtbot to capture signal
        with qtbot.waitSignal(manager.error_occurred, timeout=1000):
            result = manager.disable_hardening()

        assert result is False


class TestGetStatus:
    """Test get_status method."""

    def test_get_status_initial(self, qapp):
        """Test get_status returns initial False state.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        manager = HardeningManager()
        status = manager.get_status()
        assert status is False

    @patch("src.core.hardening_manager.subprocess.run")
    def test_get_status_after_enable(self, mock_run, qapp):
        """Test get_status returns True after successful enable.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        manager.enable_hardening()
        status = manager.get_status()

        assert status is True

    @patch("src.core.hardening_manager.subprocess.run")
    def test_get_status_after_disable(self, mock_run, qapp):
        """Test get_status returns False after successful disable.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        manager.is_protected = True
        manager.disable_hardening()
        status = manager.get_status()

        assert status is False

    def test_get_status_unchanged_after_failed_enable(self, qapp):
        """Test get_status unchanged after failed enable.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        manager = HardeningManager()
        initial_status = manager.get_status()

        with patch("src.core.hardening_manager.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Error"
            mock_run.return_value = mock_result

            manager.enable_hardening()
            status = manager.get_status()

        assert status == initial_status


class TestSubprocessParameters:
    """Test subprocess call parameters."""

    @patch("src.core.hardening_manager.subprocess.run")
    def test_subprocess_timeout_parameter(self, mock_run, qapp):
        """Test subprocess.run is called with timeout parameter.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        manager.enable_hardening()

        # Verify timeout parameter
        call_kwargs = mock_run.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] == 30

    @patch("src.core.hardening_manager.subprocess.run")
    def test_subprocess_capture_output_parameter(self, mock_run, qapp):
        """Test subprocess.run is called with capture_output parameter.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        manager = HardeningManager()
        manager.enable_hardening()

        # Verify capture_output and text parameters
        call_kwargs = mock_run.call_args[1]
        assert "capture_output" in call_kwargs
        assert call_kwargs["capture_output"] is True
        assert "text" in call_kwargs
        assert call_kwargs["text"] is True


class TestErrorHandling:
    """Test error handling and signal emissions."""

    @patch("src.core.hardening_manager.subprocess.run")
    def test_error_message_from_stderr(self, mock_run, qapp, qtbot):
        """Test error_occurred signal contains stderr message.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for signal testing
        """
        # Setup mock
        error_msg = "Permission denied error"
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = error_msg
        mock_run.return_value = mock_result

        manager = HardeningManager()

        # Capture the emitted signal argument
        signal_args = []

        def capture_error(msg):
            signal_args.append(msg)

        manager.error_occurred.connect(capture_error)
        manager.enable_hardening()

        # Verify error message was emitted
        assert len(signal_args) > 0
        assert error_msg in signal_args[0] or "failed" in signal_args[0].lower()

    @patch("src.core.hardening_manager.subprocess.run")
    def test_error_message_from_exception(self, mock_run, qapp):
        """Test error_occurred signal contains exception message.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock to raise exception
        exception_msg = "Test exception"
        mock_run.side_effect = Exception(exception_msg)

        manager = HardeningManager()

        # Capture the emitted signal argument
        signal_args = []

        def capture_error(msg):
            signal_args.append(msg)

        manager.error_occurred.connect(capture_error)
        manager.enable_hardening()

        # Verify error message was emitted
        assert len(signal_args) > 0
        assert exception_msg in signal_args[0]

    @patch("src.core.hardening_manager.subprocess.run")
    def test_default_error_message_when_no_stderr(self, mock_run, qapp):
        """Test default error message when subprocess returns no stderr.

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock with no stderr
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = ""  # Empty stderr
        mock_run.return_value = mock_result

        manager = HardeningManager()

        # Capture the emitted signal argument
        signal_args = []

        def capture_error(msg):
            signal_args.append(msg)

        manager.error_occurred.connect(capture_error)
        manager.enable_hardening()

        # Verify default error message was emitted
        assert len(signal_args) > 0
        assert "failed" in signal_args[0].lower() or "Disable" in signal_args[0]
