"""Tests for the integration layer that assembles OpenGuard's components.

The components were each tested in isolation while nothing connected them, so
the shipped application opened an empty event loop and showed no window. These
tests cover the wiring itself.
"""

import subprocess
from datetime import datetime

import pytest
from PyQt6.QtCore import QTimer

import src.app
from src.core.config_manager import ConfigManager
from src.core.hardening_manager import HardeningManager
from src.core.process_monitor import ProcessMonitor
from src.models.event import Event
from src.models.settings import Settings
from src.ui.analytics_modal import AnalyticsModal
from src.ui.main_window import MainWindow
from src.ui.onboarding_wizard import OnboardingWizard
from src.ui.settings_dialog import SettingsDialog
from src.ui.styles import get_stylesheet
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


class TestInitialStateIsHonest:
    """The interface must not claim protection that was never applied.

    MainWindow and SystemTray both start with is_protected set to True and
    paint themselves green, while HardeningManager starts False because nothing
    has run. A freshly launched OpenGuard therefore told the user they were
    protected when no firewall rule had been applied, and the toggle button
    read "Disable Protection" while clicking it would enable.
    """

    def test_window_starts_matching_the_backend(self, qapp):
        """The window must reflect real state, not an optimistic default."""
        qapp.setup_ui()

        assert qapp.main_window.is_protected == qapp.hardening_manager.is_protected

    def test_tray_starts_matching_the_backend(self, qapp):
        """The tray icon colour makes the same claim and must be as honest."""
        qapp.setup_ui()

        assert qapp.system_tray.is_protected == qapp.hardening_manager.is_protected


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


class TestHelpIsReachable:
    """The tray's "? Help" menu entry existed but its handler was a no-op."""

    def test_help_request_opens_the_project_page(self, qapp, monkeypatch):
        """Choosing Help from the tray must open the GitHub repo in the browser.

        Patching QDesktopServices.openUrl on src.app (where it is imported and
        called) rather than on a throwaway SystemTray instance means this only
        passes if the real setup_ui() code path actually wires
        system_tray.help_clicked to a handler that calls it; deleting the
        .connect(...) call in setup_ui() would fail this test.
        """
        calls = []
        monkeypatch.setattr(
            src.app.QDesktopServices, "openUrl", lambda url: calls.append(url)
        )
        qapp.setup_ui()

        qapp.system_tray.help_clicked.emit()

        assert len(calls) == 1
        assert calls[0].toString() == "https://github.com/LessTokenApp/OpenGuard"


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


class TestSettingsDialogIsReachableFromMainWindow:
    """Task 25 made Settings.systray_enabled hide the tray icon live, which made
    the tray's "⚙️ Settings" menu item the *only* way to reopen Settings once a
    user disabled the tray and saved. MainWindow now has its own Settings
    button wired to the same handler, so this must not be the only path.
    """

    def test_main_window_settings_click_opens_the_dialog(self, qapp):
        """Clicking Settings on the main window must open the same dialog the tray does."""
        qapp.setup_ui()

        qapp.main_window.settings_clicked.emit()

        assert isinstance(qapp.settings_dialog, SettingsDialog)

    def test_main_window_settings_button_still_works_with_systray_disabled(
        self, qapp, monkeypatch
    ):
        """The regression this task exists to prevent.

        With systray_enabled=False (as it would be after a user disabled and
        saved it per Task 25), the tray icon is hidden and offers no menu at
        all. MainWindow's Settings button must remain present, enabled, and
        must still open SettingsDialog through the real app.py wiring.
        """
        monkeypatch.setattr(
            ConfigManager, "load_config", lambda self: Settings(systray_enabled=False)
        )
        qapp.setup_ui()

        assert qapp.system_tray.isVisible() is False
        button = qapp.main_window.get_settings_button()
        assert button.isEnabled()

        qapp.main_window.settings_clicked.emit()

        assert isinstance(qapp.settings_dialog, SettingsDialog)


class TestAnalyticsIsReachable:
    """AnalyticsModal was implemented and tested but nothing could open it."""

    def test_analytics_request_opens_the_modal(self, qapp):
        """Choosing Analytics from the tray must open the dialog."""
        qapp.setup_ui()

        qapp.system_tray.analytics_clicked.emit()

        assert isinstance(qapp.analytics_modal, AnalyticsModal)

    def test_logged_events_are_recorded_for_analytics(self, qapp):
        """Events shown in the activity log must also be retained."""
        qapp.setup_ui()
        qapp.session_events.clear()

        qapp.hardening_manager.status_changed.emit(True)

        assert qapp.session_events, "nothing was recorded for analytics"

    def test_opening_analytics_passes_the_recorded_events(self, qapp):
        """The dialog reported zero of everything because it was never fed."""
        qapp.setup_ui()
        qapp.session_events.clear()
        qapp.hardening_manager.error_occurred.emit("something failed")

        qapp.system_tray.analytics_clicked.emit()

        assert qapp.analytics_modal.events == qapp.session_events


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
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "config_path", tmp_path / "absent" / "config.yaml")

        qapp.maybe_show_onboarding()

        assert isinstance(qapp.onboarding_wizard, OnboardingWizard)

    def test_wizard_is_skipped_when_config_exists(self, qapp, monkeypatch, tmp_path):
        """Returning users must not be sent through setup again."""
        qapp.setup_ui()
        existing = tmp_path / "config.yaml"
        existing.write_text("firewall_level: Moderate\n")
        monkeypatch.setattr(qapp.config_manager, "config_path", existing)

        qapp.maybe_show_onboarding()

        assert qapp.onboarding_wizard is None

    def test_completing_the_wizard_persists_its_choices(self, qapp, monkeypatch, tmp_path):
        """Answers given during setup must be adopted and written out."""
        qapp.setup_ui()
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

    def test_hardening_advisory_appended_to_the_activity_log(self, qapp):
        """The advisory_raised signal must be connected to the activity log."""
        qapp.setup_ui()
        qapp.main_window.activity_log.clear()

        qapp.hardening_manager.advisory_raised.emit(
            "Bu aracı, trafiği şifrelemez. Dinleme ve MITM riskini ortadan kaldırmaz."
        )

        assert "trafiği şifrelemez" in qapp.main_window.activity_log.toPlainText()


class TestProcessMonitorIsWired:
    """ProcessMonitor (Task 12) existed and was unit-tested in isolation but
    was never instantiated anywhere in app.py, so it never actually ran.
    """

    def test_setup_ui_creates_a_process_monitor(self, qapp):
        """setup_ui() must leave the app holding a real ProcessMonitor."""
        qapp.setup_ui()

        assert isinstance(qapp.process_monitor, ProcessMonitor)

    def test_setup_ui_starts_monitoring(self, qapp, monkeypatch):
        """start_monitoring() must actually be called, not merely available.

        Patching the class method (before setup_ui() creates the instance)
        means this only passes if the real app.py code path calls it; deleting
        the .start_monitoring() call in setup_ui() would fail this test.
        """
        started = []
        monkeypatch.setattr(
            ProcessMonitor, "start_monitoring", lambda self: started.append(True)
        )

        qapp.setup_ui()

        assert started, "setup_ui() never started process monitoring"

    def test_process_monitor_events_appended_to_the_activity_log(self, qapp):
        """new_events emitted on the real, app-wired ProcessMonitor must reach the log.

        Mirrors test_hardening_advisory_appended_to_the_activity_log (Task 17,
        commit d180ebc): the signal is emitted on qapp.process_monitor itself,
        the real attribute setup_ui() wires up, not a throwaway instance.
        """
        qapp.setup_ui()
        qapp.main_window.activity_log.clear()

        qapp.process_monitor.new_events.emit(
            [
                Event(
                    timestamp=datetime.now(),
                    event="Process monitoring started for OpenGuard.ps1",
                    severity="SUCCESS",
                    category="system",
                )
            ]
        )

        assert "Process monitoring started" in qapp.main_window.activity_log.toPlainText()

    def test_process_monitor_events_are_recorded_for_analytics(self, qapp):
        """Events from the real, app-wired ProcessMonitor must also be retained for analytics."""
        qapp.setup_ui()
        qapp.session_events.clear()

        qapp.process_monitor.new_events.emit(
            [
                Event(
                    timestamp=datetime.now(),
                    event="Process monitoring stopped for OpenGuard.ps1",
                    severity="SUCCESS",
                    category="system",
                )
            ]
        )

        assert qapp.session_events, "process monitor events were never recorded for analytics"

    def test_exit_requested_stops_monitoring(self, qapp, monkeypatch):
        """_on_exit_requested() must stop process monitoring before quitting."""
        qapp.setup_ui()
        stopped = []
        monkeypatch.setattr(
            qapp.process_monitor, "stop_monitoring", lambda: stopped.append(True)
        )
        monkeypatch.setattr(qapp, "quit", lambda: None)

        qapp._on_exit_requested()

        assert stopped, "_on_exit_requested() never stopped process monitoring"


class TestThemeFollowsSettings:
    """Settings.dark_mode persisted correctly but never affected the rendered UI.

    Every UI class hardcoded dark_mode=True at its get_stylesheet() call site,
    so unchecking Dark Mode and saving produced no visible change anywhere.
    """

    def test_setup_ui_applies_the_configured_dark_mode(self, qapp, monkeypatch):
        """A saved light-mode preference must produce a light-themed window from launch."""
        monkeypatch.setattr(ConfigManager, "load_config", lambda self: Settings(dark_mode=False))

        qapp.setup_ui()

        assert qapp.main_window.styleSheet() == get_stylesheet(dark_mode=False)

    def test_setup_ui_applies_the_configured_dark_mode_to_the_tray(self, qapp, monkeypatch):
        """The tray menu must also start themed according to the saved preference."""
        monkeypatch.setattr(ConfigManager, "load_config", lambda self: Settings(dark_mode=False))

        qapp.setup_ui()

        assert qapp.system_tray.tray_menu.styleSheet() == get_stylesheet(dark_mode=False)

    def test_settings_dialog_opens_using_the_settings_at_open_time(self, qapp):
        """The dialog is created lazily; it must read dark_mode as of the open, not launch."""
        qapp.setup_ui()
        qapp.settings.dark_mode = False

        qapp.system_tray.settings_clicked.emit()

        assert qapp.settings_dialog.styleSheet() == get_stylesheet(dark_mode=False)

    def test_analytics_modal_opens_using_the_settings_at_open_time(self, qapp):
        """The modal is created lazily; it must read dark_mode as of the open, not launch."""
        qapp.setup_ui()
        qapp.settings.dark_mode = False

        qapp.system_tray.analytics_clicked.emit()

        assert qapp.analytics_modal.styleSheet() == get_stylesheet(dark_mode=False)

    def test_onboarding_wizard_opens_using_the_current_dark_mode(self, qapp, monkeypatch, tmp_path):
        """The wizard is only constructed on a first run; it must still honour the setting."""
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "config_path", tmp_path / "absent" / "config.yaml")
        qapp.settings.dark_mode = False

        qapp.maybe_show_onboarding()

        assert qapp.onboarding_wizard.styleSheet() == get_stylesheet(dark_mode=False)

    def test_saving_a_flipped_dark_mode_retheme_the_open_main_window_live(self, qapp, monkeypatch):
        """Saving Settings with Dark Mode unchecked must re-theme the already-open window.

        This is the core regression test: main_window.styleSheet() must actually
        change as a result of the save, without the window being reconstructed.
        """
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        original_window = qapp.main_window
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.dark_mode_check.setChecked(False)

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.main_window is original_window, "window was reconstructed instead of re-themed"
        assert qapp.main_window.styleSheet() == get_stylesheet(dark_mode=False)

    def test_saving_a_flipped_dark_mode_retheme_the_tray_menu_live(self, qapp, monkeypatch):
        """Saving Settings with Dark Mode unchecked must re-theme the already-open tray menu."""
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.dark_mode_check.setChecked(False)

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.system_tray.tray_menu.styleSheet() == get_stylesheet(dark_mode=False)

    def test_saving_back_to_dark_mode_retheme_live_too(self, qapp, monkeypatch):
        """The re-theming must work symmetrically, not just for the light-mode direction."""
        monkeypatch.setattr(ConfigManager, "load_config", lambda self: Settings(dark_mode=False))
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.dark_mode_check.setChecked(True)

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.main_window.styleSheet() == get_stylesheet(dark_mode=True)

    def test_saving_retheme_the_cached_settings_dialog(self, qapp, monkeypatch):
        """The settings dialog itself is cached across opens and must be re-themed too."""
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.dark_mode_check.setChecked(False)

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.settings_dialog.styleSheet() == get_stylesheet(dark_mode=False)

    def test_saving_retheme_the_cached_analytics_modal(self, qapp, monkeypatch):
        """A previously opened analytics modal is cached and must be re-themed on save too."""
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        qapp.system_tray.analytics_clicked.emit()
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.dark_mode_check.setChecked(False)

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.analytics_modal.styleSheet() == get_stylesheet(dark_mode=False)


class TestAutoStartFollowsSettings:
    """Settings.auto_start persisted correctly but never registered/removed a
    real Windows startup entry - it was purely cosmetic. Task 27 wires
    startup_manager.apply() into both the initial reconciliation on launch
    and the live save path, mirroring dark_mode (Task 20) and systray_enabled
    (Task 25).
    """

    def test_setup_ui_reconciles_startup_registration_with_loaded_settings(
        self, qapp, monkeypatch
    ):
        """setup_ui() must call startup_manager.apply() with the loaded auto_start value.

        Patching the module-level function before setup_ui() runs means this
        only passes if the real app.py code path calls it; deleting the
        apply() call in setup_ui() would fail this test.
        """
        monkeypatch.setattr(
            ConfigManager, "load_config", lambda self: Settings(auto_start=False)
        )
        calls = []
        monkeypatch.setattr(src.app.startup_manager, "apply", lambda enabled: calls.append(enabled))

        qapp.setup_ui()

        assert calls == [False]

    def test_saving_settings_reapplies_startup_registration_live(self, qapp, monkeypatch):
        """Flipping auto_start in the dialog and saving must call apply() again
        through the real _on_settings_saved() path with the new value.
        """
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        calls = []
        monkeypatch.setattr(src.app.startup_manager, "apply", lambda enabled: calls.append(enabled))
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.auto_start_check.setChecked(False)

        qapp.settings_dialog.settings_changed.emit()

        assert calls == [False]


class TestSystrayEnabledFollowsSettings:
    """Settings.systray_enabled persisted correctly but never affected the live tray icon.

    setup_ui() only reads it once, at launch, to decide whether to call
    system_tray.show(). Toggling "System tray integration" in Settings and
    saving had no live effect until the app was restarted.
    """

    def test_saving_settings_with_systray_disabled_hides_the_live_tray_icon(
        self, qapp, monkeypatch
    ):
        """Unchecking the tray checkbox and saving must hide the already-shown tray icon.

        This is the core regression test: system_tray.isVisible() must actually
        change as a result of the save.
        """
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        assert qapp.system_tray.isVisible() is True
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.systray_check.setChecked(False)

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.system_tray.isVisible() is False

    def test_saving_settings_with_systray_enabled_shows_the_hidden_tray_icon(
        self, qapp, monkeypatch
    ):
        """Re-checking the tray checkbox and saving must show a previously hidden tray icon."""
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        qapp.system_tray.hide()
        assert qapp.system_tray.isVisible() is False
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.systray_check.setChecked(True)

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.system_tray.isVisible() is True

    def test_saving_settings_with_systray_left_enabled_is_a_no_op(self, qapp, monkeypatch):
        """Saving with the checkbox unchanged (True -> True) must not error and must stay visible."""
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        qapp.system_tray.settings_clicked.emit()

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.system_tray.isVisible() is True

    def test_saving_settings_with_systray_left_disabled_is_a_no_op(self, qapp, monkeypatch):
        """Saving with the checkbox unchanged (False -> False) must not error and stay hidden."""
        qapp.setup_ui()
        monkeypatch.setattr(qapp.config_manager, "save_config", lambda s: True)
        qapp.system_tray.hide()
        qapp.system_tray.settings_clicked.emit()
        qapp.settings_dialog.systray_check.setChecked(False)

        qapp.settings_dialog.settings_changed.emit()

        assert qapp.system_tray.isVisible() is False
