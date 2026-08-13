"""OpenGuard main application class."""

import sys
from datetime import datetime

from PyQt6.QtWidgets import QApplication

from src.core.config_manager import ConfigManager
from src.core.hardening_manager import HardeningManager
from src.models.event import Event
from src.models.settings import Settings
from src.ui.analytics_modal import AnalyticsModal
from src.ui.main_window import MainWindow
from src.ui.onboarding_wizard import OnboardingWizard
from src.ui.settings_dialog import SettingsDialog
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
        self.session_events: list[Event] = []

    def setup_ui(self) -> None:
        """Build the user interface and connect it to the backend.

        Safe to call more than once; the existing window is kept.
        """
        if self.main_window is not None:
            return

        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_config()

        self.hardening_manager = HardeningManager()
        self.main_window = MainWindow()

        self.system_tray = SystemTray()

        self.main_window.toggle_protection_clicked.connect(self._on_toggle_requested)
        self.system_tray.toggle_clicked.connect(self._on_toggle_requested)
        self.system_tray.settings_clicked.connect(self._on_settings_requested)
        self.system_tray.analytics_clicked.connect(self._on_analytics_requested)
        self.system_tray.exit_clicked.connect(self._on_exit_requested)

        self.hardening_manager.status_changed.connect(self.main_window.set_protection_status)
        self.hardening_manager.status_changed.connect(self.system_tray.set_protection_status)
        self.hardening_manager.status_changed.connect(self._on_status_changed)
        self.hardening_manager.error_occurred.connect(self._on_error)

        if self.settings.systray_enabled:
            self.system_tray.show()

    def _on_toggle_requested(self) -> None:
        """Enable or disable hardening depending on the current state.

        The manager holds the authoritative status, since it reflects what was
        actually applied to the system rather than what the window last drew.
        """
        if self.hardening_manager.is_protected:
            self.hardening_manager.disable_hardening()
        else:
            self.hardening_manager.enable_hardening(level=self.settings.firewall_level)

    def _on_settings_requested(self) -> None:
        """Open the settings dialog, creating it on first use."""
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(initial_settings=self.settings)
            self.settings_dialog.settings_changed.connect(self._on_settings_saved)

        self.settings_dialog.show()
        self.settings_dialog.raise_()

    def _on_settings_saved(self) -> None:
        """Adopt and persist the preferences edited in the dialog."""
        self.settings = self.settings_dialog.get_settings()
        self.config_manager.save_config(self.settings)

    def _on_analytics_requested(self) -> None:
        """Open the analytics dialog, creating it on first use."""
        if self.analytics_modal is None:
            self.analytics_modal = AnalyticsModal()

        self.analytics_modal.set_events(self.session_events)
        self.analytics_modal.show()
        self.analytics_modal.raise_()

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

        self.onboarding_wizard = OnboardingWizard()
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

        self.session_events.append(event)
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
