"""OpenGuard main application class."""

import sys
from datetime import datetime

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication

from src.core import startup_manager
from src.core.analytics_engine import AnalyticsEngine
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


class OpenGuardApp(QApplication):
    """Main application class for OpenGuard.

    Inherits from QApplication and manages the application lifecycle,
    including initialization and main event loop execution.
    """

    def __init__(self) -> None:
        """Initialize the OpenGuard application.

        Sets up application metadata and style. The interface itself is built
        by setup_ui(), which run() calls, so constructing the application does
        not create windows.
        """
        super().__init__(sys.argv)

        # Set application metadata
        self.setApplicationName("OpenGuard")
        self.setApplicationVersion("0.7.0")

        # Use Fusion style for modern cross-platform appearance
        self.setStyle("Fusion")

        self.main_window: MainWindow | None = None
        self.hardening_manager: HardeningManager | None = None
        self.config_manager: ConfigManager | None = None
        self.settings: Settings | None = None
        self.system_tray: SystemTray | None = None
        self.settings_dialog: SettingsDialog | None = None
        self.analytics_modal: AnalyticsModal | None = None
        self.onboarding_wizard: OnboardingWizard | None = None
        self.analytics_engine: AnalyticsEngine | None = None
        self.process_monitor: ProcessMonitor | None = None

    @property
    def session_events(self) -> list[Event]:
        """Events recorded this run, held by the engine that persists them."""
        if self.analytics_engine is None:
            return []

        return self.analytics_engine.events

    def setup_ui(self) -> None:
        """Build the user interface and connect it to the backend.

        Safe to call more than once; the existing window is kept.
        """
        if self.main_window is not None:
            return

        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_config()

        self.analytics_engine = AnalyticsEngine()

        self.hardening_manager = HardeningManager()
        self.main_window = MainWindow(dark_mode=self.settings.dark_mode)

        self.system_tray = SystemTray(dark_mode=self.settings.dark_mode)

        self.main_window.toggle_protection_clicked.connect(self._on_toggle_requested)
        self.main_window.settings_clicked.connect(self._on_settings_requested)
        self.system_tray.toggle_clicked.connect(self._on_toggle_requested)
        self.system_tray.settings_clicked.connect(self._on_settings_requested)
        self.system_tray.analytics_clicked.connect(self._on_analytics_requested)
        self.system_tray.help_clicked.connect(self._on_help_requested)
        self.system_tray.exit_clicked.connect(self._on_exit_requested)

        self.hardening_manager.status_changed.connect(self.main_window.set_protection_status)
        self.hardening_manager.status_changed.connect(self.system_tray.set_protection_status)
        self.hardening_manager.status_changed.connect(self._on_status_changed)
        self.hardening_manager.error_occurred.connect(self._on_error)
        self.hardening_manager.advisory_raised.connect(self._on_advisory)

        self.process_monitor = ProcessMonitor()
        self.process_monitor.new_events.connect(self._on_process_monitor_events)

        # Both widgets default to showing protection as active. Nothing has run
        # at this point, so publish the manager's real state before the window
        # is ever seen rather than claiming safety that was never applied.
        self._publish_status(self.hardening_manager.get_status())

        if self.settings.systray_enabled:
            self.system_tray.show()

        # Reconcile the actual Windows startup registration with the
        # loaded/default setting on every launch, the same pattern used for
        # dark_mode (Task 20) and systray_enabled above (Task 25).
        startup_manager.apply(self.settings.auto_start)

        # App-lifetime monitoring: HardeningManager.enable_hardening()/
        # disable_hardening() are short-lived synchronous subprocess.run()
        # calls that return after the PowerShell script has already exited,
        # so there is no meaningful "protection is currently active" window
        # to tie ProcessMonitor's own start/stop to. It runs for as long as
        # the application does instead.
        self.process_monitor.start_monitoring()

    def _on_toggle_requested(self) -> None:
        """Enable or disable hardening depending on the current state.

        The manager holds the authoritative status, since it reflects what was
        actually applied to the system rather than what the window last drew.
        """
        if self.hardening_manager.is_protected:
            self.hardening_manager.disable_hardening()
        else:
            self.hardening_manager.enable_hardening(level=self.settings.firewall_level)

    def _publish_status(self, is_protected: bool) -> None:
        """Push a protection state to every widget that displays it.

        Args:
            is_protected: Whether protection is currently active.
        """
        self.main_window.set_protection_status(is_protected)
        self.system_tray.set_protection_status(is_protected)

    def _on_settings_requested(self) -> None:
        """Open the settings dialog, creating it on first use."""
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(
                initial_settings=self.settings, dark_mode=self.settings.dark_mode
            )
            self.settings_dialog.settings_changed.connect(self._on_settings_saved)

        self.settings_dialog.show()
        self.settings_dialog.raise_()

    def _on_settings_saved(self) -> None:
        """Adopt and persist the preferences edited in the dialog.

        Also re-applies the theme live to the already-open, long-lived widgets
        (the main window and the tray menu) so a Dark Mode change takes effect
        immediately rather than only the next time those widgets are rebuilt,
        and shows or hides the tray icon so a System tray integration change
        takes effect immediately too, rather than only on the next launch.
        """
        self.settings = self.settings_dialog.get_settings()
        self.config_manager.save_config(self.settings)

        stylesheet = get_stylesheet(dark_mode=self.settings.dark_mode)
        self.main_window.setStyleSheet(stylesheet)
        self.system_tray.tray_menu.setStyleSheet(stylesheet)

        # Dialogs created lazily on first open are cached; re-theme the cached
        # instance too so the setting takes effect immediately if it's still open.
        if self.settings_dialog is not None:
            self.settings_dialog.setStyleSheet(stylesheet)
        if self.analytics_modal is not None:
            self.analytics_modal.setStyleSheet(stylesheet)

        # isVisible() is the tray icon's own source of truth, so acting only
        # on a change avoids a redundant show()/hide() when the setting was
        # saved unchanged.
        if self.settings.systray_enabled:
            if not self.system_tray.isVisible():
                self.system_tray.show()
        elif self.system_tray.isVisible():
            self.system_tray.hide()

        # Toggling Auto-start on login and saving must take effect
        # immediately, the same as dark_mode and systray_enabled above.
        startup_manager.apply(self.settings.auto_start)

    def _on_analytics_requested(self) -> None:
        """Open the analytics dialog, creating it on first use."""
        if self.analytics_modal is None:
            self.analytics_modal = AnalyticsModal(dark_mode=self.settings.dark_mode)

        self.analytics_modal.set_events(self.session_events)
        self.analytics_modal.show()
        self.analytics_modal.raise_()

    def _on_help_requested(self) -> None:
        """Open the project's GitHub page in the user's default browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/LessTokenApp/OpenGuard"))

    def is_first_run(self) -> bool:
        """Report whether this looks like the user's first launch.

        Absence of a saved configuration is the signal; the onboarding wizard
        writes one when it completes, so it is offered only once.

        Returns:
            bool: True when no configuration file exists yet.
        """
        return not self.config_manager.config_path.exists()

    def maybe_show_onboarding(self) -> None:
        """Show first-run setup, but only to users who have not seen it."""
        if not self.is_first_run():
            return

        self.onboarding_wizard = OnboardingWizard(dark_mode=self.settings.dark_mode)
        self.onboarding_wizard.completed.connect(self._on_onboarding_completed)
        self.onboarding_wizard.show()

    def _on_onboarding_completed(self, settings: Settings) -> None:
        """Adopt and persist the choices made during first-run setup.

        Writing the file also marks the run as no longer being the first.

        Args:
            settings: Configuration assembled by the wizard.
        """
        self.settings = settings
        self.config_manager.save_config(settings)

    def _on_exit_requested(self) -> None:
        """Quit the application.

        Indirect so the call resolves at emit time rather than at connect time.
        """
        self.process_monitor.stop_monitoring()
        self.quit()

    def _on_status_changed(self, is_protected: bool) -> None:
        """Record a protection change in the activity log.

        Args:
            is_protected: Whether protection is now active.
        """
        description = "Protection enabled" if is_protected else "Protection disabled"
        self._log(description, "SUCCESS")

    def _on_error(self, message: str) -> None:
        """Surface a backend failure to the user.

        error_occurred previously had no receiver, so every failure was silent.

        Args:
            message: Error text reported by the backend.
        """
        self._log(message, "ERROR")

    def _on_advisory(self, advisory_text: str) -> None:
        """Record a hardening advisory in the activity log.

        The advisory describes the limitations of the hardening applied.

        Args:
            advisory_text: Advisory text from the hardening backend.
        """
        self._log(advisory_text, "WARN")

    def _on_process_monitor_events(self, events: list[Event]) -> None:
        """Record and display events reported by the process monitor.

        Duplicates the record+display logic in _log() rather than calling it,
        since _log() builds its own Event from a (description, severity) pair
        and does not accept a pre-built Event.

        Args:
            events: Events emitted by ProcessMonitor.
        """
        for event in events:
            self.analytics_engine.record(event)
            self.main_window.add_activity_log_entry(event)

    def _log(self, description: str, severity: str) -> None:
        """Append an entry to the activity log.

        Args:
            description: Human-readable description of what happened.
            severity: One of "SUCCESS", "WARN" or "ERROR".
        """
        event = Event(
            timestamp=datetime.now(),
            event=description,
            severity=severity,
            category="system",
        )

        self.analytics_engine.record(event)
        self.main_window.add_activity_log_entry(event)

    def run(self) -> int:
        """Show main window and start the event loop.

        Returns:
            int: Exit code from the Qt event loop (0 for normal exit)
        """
        self.setup_ui()
        self.main_window.show()
        self.maybe_show_onboarding()

        return self.exec()
