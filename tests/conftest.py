"""Pytest configuration and fixtures for OpenGuard tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PyQt6.QtWidgets import QApplication

from src.app import OpenGuardApp


@pytest.fixture(autouse=True)
def stub_process_monitor_subprocess(monkeypatch):
    """Prevent ProcessMonitor from spawning a real PowerShell subprocess.

    setup_ui() now calls process_monitor.start_monitoring() itself (Task 24),
    which most of the app-wiring suite exercises indirectly through
    qapp.setup_ui(). Without this, every such test would launch a real,
    infinite-loop PowerShell child process that nothing in the suite ever
    terminates.

    process_monitor.py calls the shared, global `subprocess` module, the same
    one other tests use to shell out to real powershell.exe (e.g.
    test_powershell_scripts_parse.py via subprocess.run(), which uses Popen
    internally, and whose command line also happens to mention the literal
    string "OpenGuard.ps1" as a path argument). So this only stubs the exact
    polling-loop command ProcessMonitor launches ("while ($true) { ... }",
    unique to it) and passes every other call through to the real
    subprocess.Popen unchanged.
    """
    import subprocess as subprocess_module

    real_popen = subprocess_module.Popen

    def fake_popen(cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and any("while ($true)" in str(part) for part in cmd):
            mock_process = MagicMock()
            mock_process.poll.return_value = None
            return mock_process
        return real_popen(cmd, *args, **kwargs)

    monkeypatch.setattr("src.core.process_monitor.subprocess.Popen", fake_popen)


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Point the home directory at a throwaway path for every test.

    Configuration and the event log both live under ~/.openguard by default,
    so without this a test run edits the config of whoever ran it and fills
    their event history with fabricated events.
    """
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)

    return home


@pytest.fixture(scope="session")
def qapp():
    """Create an OpenGuardApp instance for testing.

    This fixture overrides the default pytest-qt qapp fixture to use
    our custom OpenGuardApp class instead of the standard QApplication.

    Yields:
        OpenGuardApp: The application instance for tests
    """
    # Check if there's already a QApplication instance
    app = QApplication.instance()
    if app is None:
        # Create new instance if none exists
        app = OpenGuardApp()
    yield app
    # Clean up after all tests
    app.quit()


@pytest.fixture(autouse=True)
def unbuilt_app(qapp):
    """Return the application to its pre-setup_ui() state after each test.

    Qt allows one QApplication per process, so the app instance is shared for
    the whole session. Without this, a test that builds the UI leaves windows
    and a wired backend behind, and later tests pass or fail depending on the
    order they happen to run in.
    """
    yield

    if qapp.main_window is not None:
        qapp.main_window.close()
    if qapp.system_tray is not None:
        qapp.system_tray.hide()
    if qapp.process_monitor is not None:
        qapp.process_monitor.stop_monitoring()

    qapp.main_window = None
    qapp.hardening_manager = None
    qapp.config_manager = None
    qapp.settings = None
    qapp.system_tray = None
    qapp.settings_dialog = None
    qapp.analytics_modal = None
    qapp.onboarding_wizard = None
    qapp.analytics_engine = None
    qapp.process_monitor = None
