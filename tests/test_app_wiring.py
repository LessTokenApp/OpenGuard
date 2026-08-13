"""Tests for the integration layer that assembles OpenGuard's components.

The components were each tested in isolation while nothing connected them, so
the shipped application opened an empty event loop and showed no window. These
tests cover the wiring itself.
"""

import subprocess

import pytest
from PyQt6.QtCore import QTimer

from src.core.hardening_manager import HardeningManager
from src.models.settings import Settings
from src.ui.analytics_modal import AnalyticsModal
from src.ui.main_window import MainWindow
from src.ui.onboarding_wizard import OnboardingWizard
from src.ui.settings_dialog import SettingsDialog
from src.ui.systray import SystemTray


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

    def test_run_offers_onboarding(self, qapp, monkeypatch):
        """First-run setup is worthless if launching never triggers it."""
        qapp.main_window = None
        offered = []
        monkeypatch.setattr(qapp, "maybe_show_onboarding", lambda: offered.append(True))
        QTimer.singleShot(0, qapp.quit)

        qapp.run()

        assert offered, "run() never considered showing onboarding"

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


class TestSettingsAreLoaded:
    """Saved preferences must reach the components that act on them."""

    def test_setup_ui_loads_settings(self, qapp):
        """The application must hold the user's settings after building."""
        qapp.setup_ui()

        assert isinstance(qapp.settings, Settings)

    def test_configured_firewall_level_is_used_when_enabling(self, qapp, stub_backend):
        """Choosing a level in settings must change what the backend is asked for.

        The level was previously left at the method default, so the preference
        had no effect on what was applied.
        """
        qapp.setup_ui()
        qapp.settings.firewall_level = "Basic"
        qapp.hardening_manager.is_protected = False

        qapp.main_window.toggle_protection_clicked.emit()

        assert "Basic" in stub_backend[-1]


class TestSystemTrayIsWired:
    """The tray icon exists in the codebase but nothing ever created it."""

    def test_setup_ui_creates_a_system_tray(self, qapp):
        """A tray icon must be created when the user has it enabled."""
        qapp.setup_ui()

        assert isinstance(qapp.system_tray, SystemTray)

    def test_tray_toggle_drives_the_backend(self, qapp, stub_backend):
        """The tray's toggle must do the same work as the window's."""
        qapp.setup_ui()
        qapp.hardening_manager.is_protected = False

        qapp.system_tray.toggle_clicked.emit()

        assert stub_backend, "tray toggle never reached the backend"
        assert "Enable" in stub_backend[-1]

    def test_status_change_updates_the_tray(self, qapp):
        """The tray shows protection state, so it must follow the manager."""
        qapp.setup_ui()
        qapp.system_tray.set_protection_status(True)

        qapp.hardening_manager.status_changed.emit(False)

        assert qapp.system_tray.is_protected is False

    def test_tray_exit_quits_the_application(self, qapp, monkeypatch):
        """Exit must actually close the program."""
        qapp.setup_ui()
        quit_calls = []
        monkeypatch.setattr(qapp, "quit", lambda: quit_calls.append(True))

        qapp.system_tray.exit_clicked.emit()

        assert quit_calls


class TestSettingsDialogIsReachable:
    """SettingsDialog was implemented and tested but had no entry point."""

    def test_settings_request_opens_the_dialog(self, qapp):
        """Choosing settings from the tray must open the dialog."""
        qapp.setup_ui()

        qapp.system_tray.settings_clicked.emit()

        assert isinstance(qapp.settings_dialog, SettingsDialog)

    def test_saving_the_dialog_updates_application_settings(self, qapp, monkeypatch):
        """Edited preferences must replace the ones the app is using."""
        qapp.setup_ui()
        saved = []
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: saved.append(s) or True)
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.set_firewall_level("Relaxed")

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.settings.firewall_level == "Relaxed"
        assert saved, "edited settings were never persisted"


class TestAnalyticsIsReachable:
    """AnalyticsModal was implemented and tested but nothing could open it."""

    def test_analytics_request_opens_the_modal(self, qapp):
        """Choosing Analytics from the tray must open the dialog."""
        qapp.setup_ui()

        qapp.system_tray.analytics_clicked.emit()

        assert isinstance(qapp.analytics_modal, AnalyticsModal)


class TestFirstRunOnboarding:
    """The wizard was written for first-run setup and never shown."""

    def test_wizard_is_offered_when_no_config_exists(self, qapp, monkeypatch, tmp_path):
        """A machine with no saved config is a first run."""
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "config_path", tmp_path / "absent" / "config.yaml")

        assert qapp.is_first_run() is True

    def test_existing_config_is_not_a_first_run(self, qapp, monkeypatch, tmp_path):
        """An existing config must not re-run onboarding on every launch."""
        qapp.setup_ui()
        existing = tmp_path / "config.yaml"
        existing.write_text("firewall_level: Moderate\n")
        monkeypatch.setattr(qapp.config_manager, "config_path", existing)

        assert qapp.is_first_run() is False

    def test_wizard_is_created_on_a_first_run(self, qapp, monkeypatch, tmp_path):
        """The wizard must be built and shown, not merely available."""
        qapp.onboarding_wizard = None
        monkeypatch.setattr(qapp.config_manager, "config_path", tmp_path / "absent" / "config.yaml")

        qapp.maybe_show_onboarding()

        assert isinstance(qapp.onboarding_wizard, OnboardingWizard)

    def test_wizard_is_skipped_when_config_exists(self, qapp, monkeypatch, tmp_path):
        """Returning users must not be sent through setup again."""
        qapp.onboarding_wizard = None
        existing = tmp_path / "config.yaml"
        existing.write_text("firewall_level: Moderate\n")
        monkeypatch.setattr(qapp.config_manager, "config_path", existing)

        qapp.maybe_show_onboarding()

        assert qapp.onboarding_wizard is None

    def test_completing_the_wizard_persists_its_choices(self, qapp, monkeypatch, tmp_path):
        """Answers given during setup must be adopted and written out."""
        qapp.onboarding_wizard = None
        monkeypatch.setattr(qapp.config_manager, "config_path", tmp_path / "absent" / "config.yaml")
        saved = []
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: saved.append(s) or True)
        qapp.maybe_show_onboarding()

        qapp.onboarding_wizard.completed.emit(Settings(firewall_level="Relaxed"))

        assert qapp.settings.firewall_level == "Relaxed"
        assert saved, "onboarding answers were never persisted"


class TestActivityIsReported:
    """The activity log and error signal must not be write-only."""

    def test_status_change_appends_to_the_activity_log(self, qapp):
        """The user needs feedback that something happened."""
        qapp.setup_ui()
        qapp.main_window.activity_log.clear()

        qapp.hardening_manager.status_changed.emit(True)

        assert qapp.main_window.activity_log.toPlainText().strip()

    def test_backend_errors_are_surfaced(self, qapp):
        """error_occurred previously went nowhere, hiding every failure."""
        qapp.setup_ui()
        qapp.main_window.activity_log.clear()

        qapp.hardening_manager.error_occurred.emit("backend exploded")

        assert "backend exploded" in qapp.main_window.activity_log.toPlainText()
