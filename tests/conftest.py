"""Pytest configuration and fixtures for OpenGuard tests."""

from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

from src.app import OpenGuardApp


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

    qapp.main_window = None
    qapp.hardening_manager = None
    qapp.config_manager = None
    qapp.settings = None
    qapp.system_tray = None
    qapp.settings_dialog = None
    qapp.analytics_modal = None
    qapp.onboarding_wizard = None
    qapp.analytics_engine = None
