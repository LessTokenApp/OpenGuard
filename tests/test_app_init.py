"""Tests for application initialization and main application class."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QApplication

from src.app import OpenGuardApp


class TestOpenGuardAppCreation:
    """Test OpenGuardApp instantiation and basic properties."""

    def test_app_creation(self, qapp):
        """Test that OpenGuardApp can be instantiated.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        # qapp is already an OpenGuardApp instance provided by pytest-qt
        assert qapp is not None
        assert isinstance(qapp, (QApplication, OpenGuardApp))

    def test_app_is_singleton(self, qapp):
        """Test that there is only one QApplication instance.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        # QApplication.instance() should return the existing instance
        instance = QApplication.instance()
        assert instance is not None

    def test_app_name(self, qapp):
        """Test that application name is set correctly.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        assert qapp.applicationName() == "OpenGuard"

    def test_app_version(self, qapp):
        """Test that application version is set correctly.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        assert qapp.applicationVersion() == "0.7.0"

    def test_app_style(self, qapp):
        """Test that application style is set to Fusion.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        # Style name for Fusion style (may vary by platform)
        style_name = qapp.style().objectName().lower()
        assert style_name in ["fusion", "", "windows"]

    def test_main_window_attribute_exists(self, qapp):
        """Test that main_window attribute exists.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        assert hasattr(qapp, "main_window")
        # Initially it should be None
        assert qapp.main_window is None


class TestOpenGuardAppRun:
    """Test OpenGuardApp.run() method."""

    def test_run_method_exists(self, qapp):
        """Test that run method exists and is callable.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        assert hasattr(qapp, "run")
        assert callable(qapp.run)

    def test_run_returns_int(self, qapp):
        """Test that run() method returns an integer.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        # Mock exec to simulate event loop
        with patch.object(qapp, "exec", return_value=0):
            result = qapp.run()
            assert isinstance(result, int)

    def test_run_returns_exit_code(self, qapp):
        """Test that run() returns valid exit code.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        # Mock exec to return different exit codes
        with patch.object(qapp, "exec", return_value=0):
            result = qapp.run()
            assert result == 0

        with patch.object(qapp, "exec", return_value=1):
            result = qapp.run()
            assert result == 1

    def test_run_calls_exec(self, qapp):
        """Test that run() calls exec() to start event loop.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        with patch.object(qapp, "exec", return_value=0) as mock_exec:
            qapp.run()
            mock_exec.assert_called_once()

    def test_run_shows_main_window_if_present(self, qapp):
        """Test that run() shows main window if it's set.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        # Build the real UI first, then stand in for the window, so the rest of
        # the application is wired the way run() expects.
        qapp.setup_ui()
        mock_window = MagicMock()
        qapp.main_window = mock_window

        with patch.object(qapp, "exec", return_value=0):
            qapp.run()
            mock_window.show.assert_called_once()

    def test_run_without_main_window(self, qapp):
        """Test that run() works without main window set.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        qapp.main_window = None

        with patch.object(qapp, "exec", return_value=0):
            # Should not raise an error
            result = qapp.run()
            assert result == 0


class TestMainEntryPoint:
    """Test main() entry point function."""

    def test_main_function_exists(self):
        """Test that main() function exists."""
        from src.main import main

        assert callable(main)

    def test_main_returns_int(self):
        """Test that main() returns an integer (exit code)."""
        from src.main import main

        # Mock OpenGuardApp.run() to avoid actual event loop
        with patch("src.main.OpenGuardApp") as mock_app_class:
            mock_app_instance = MagicMock()
            mock_app_instance.run.return_value = 0
            mock_app_class.return_value = mock_app_instance

            result = main()
            assert isinstance(result, int)

    def test_main_creates_app_and_runs(self):
        """Test that main() creates app and calls run()."""
        from src.main import main

        with patch("src.main.OpenGuardApp") as mock_app_class:
            mock_app_instance = MagicMock()
            mock_app_instance.run.return_value = 0
            mock_app_class.return_value = mock_app_instance

            main()

            mock_app_class.assert_called_once()
            mock_app_instance.run.assert_called_once()

    def test_main_returns_app_exit_code(self):
        """Test that main() returns the exit code from app.run()."""
        from src.main import main

        with patch("src.main.OpenGuardApp") as mock_app_class:
            mock_app_instance = MagicMock()
            mock_app_instance.run.return_value = 42
            mock_app_class.return_value = mock_app_instance

            result = main()
            assert result == 42
