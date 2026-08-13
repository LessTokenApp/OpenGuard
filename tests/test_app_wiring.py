"""Tests for the integration layer that assembles OpenGuard's components.

The components were each tested in isolation while nothing connected them, so
the shipped application opened an empty event loop and showed no window. These
tests cover the wiring itself.
"""

import subprocess

import pytest
from PyQt6.QtCore import QTimer

from src.core.hardening_manager import HardeningManager
from src.ui.main_window import MainWindow


@pytest.fixture
def stub_backend(monkeypatch):
    """Stop hardening calls from touching the machine's firewall or DNS."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


class TestApplicationBuildsUI:
    """The application must actually construct its user interface."""

    def test_setup_ui_creates_a_main_window(self, qapp):
        """setup_ui() must leave the app holding a real MainWindow."""
        qapp.setup_ui()

        assert isinstance(qapp.main_window, MainWindow)

    def test_setup_ui_is_idempotent(self, qapp):
        """Calling setup_ui() twice must not replace the existing window."""
        qapp.setup_ui()
        first = qapp.main_window

        qapp.setup_ui()

        assert qapp.main_window is first

    def test_setup_ui_creates_a_hardening_manager(self, qapp):
        """The window is useless without the component that does the work."""
        qapp.setup_ui()

        assert isinstance(qapp.hardening_manager, HardeningManager)


class TestToggleReachesTheBackend:
    """The toggle button must drive the hardening manager."""

    def test_toggle_enables_when_not_protected(self, qapp, stub_backend):
        """Toggling while unprotected must request Enable."""
        qapp.setup_ui()
        qapp.hardening_manager.is_protected = False

        qapp.main_window.toggle_protection_clicked.emit()

        assert stub_backend, "toggle never reached the backend"
        assert "Enable" in stub_backend[-1]

    def test_toggle_disables_when_protected(self, qapp, stub_backend):
        """Toggling while protected must request Disable."""
        qapp.setup_ui()
        qapp.hardening_manager.is_protected = True

        qapp.main_window.toggle_protection_clicked.emit()

        assert stub_backend, "toggle never reached the backend"
        assert "Disable" in stub_backend[-1]


class TestRunShowsTheWindow:
    """The shipped build opened an event loop and displayed nothing.

    run() showed a window only if one had already been assigned, and nothing
    ever assigned one, so the executable sat invisible in Task Manager.
    """

    def test_run_builds_the_ui_when_it_has_not_been_built(self, qapp):
        """run() must construct the interface rather than assume it exists."""
        qapp.main_window = None
        QTimer.singleShot(0, qapp.quit)

        qapp.run()

        assert qapp.main_window is not None

    def test_window_is_visible_while_the_event_loop_runs(self, qapp):
        """A user must actually see something while the application is running.

        Visibility is sampled from inside the loop: Qt hides top-level windows
        as it shuts down, so checking after run() returns would always fail
        regardless of whether anything was ever displayed.
        """
        qapp.main_window = None
        observed = {}

        def probe():
            observed["visible"] = qapp.main_window.isVisible()
            observed["top_level"] = len(qapp.topLevelWidgets())
            qapp.quit()

        QTimer.singleShot(0, probe)

        qapp.run()

        assert observed["visible"], "the main window was never shown"
        assert observed["top_level"] >= 1


class TestStatusFlowsBackToTheWindow:
    """Status reported by the manager must reach the user interface."""

    def test_status_change_updates_the_window(self, qapp):
        """A status change on the manager must update the window."""
        qapp.setup_ui()
        qapp.main_window.set_protection_status(True)

        qapp.hardening_manager.status_changed.emit(False)

        assert qapp.main_window.is_protected is False
