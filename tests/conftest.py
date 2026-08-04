"""Pytest configuration and fixtures for OpenGuard tests."""

import sys

import pytest
from PyQt6.QtWidgets import QApplication

from src.app import OpenGuardApp


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
