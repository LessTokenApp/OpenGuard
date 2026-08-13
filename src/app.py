"""OpenGuard main application class."""

import sys

from PyQt6.QtWidgets import QApplication

from src.core.hardening_manager import HardeningManager
from src.ui.main_window import MainWindow


class OpenGuardApp(QApplication):
    """Main application class for OpenGuard.

    Inherits from QApplication and manages the application lifecycle,
    including initialization and main event loop execution.
    """

    def __init__(self) -> None:
        """Initialize the OpenGuard application.

        Sets up the Qt application with:
        - Application name and version
        - Modern Fusion style for cross-platform appearance
        - Placeholder for main window (to be set by task 3)
        """
        super().__init__(sys.argv)

        # Set application metadata
        self.setApplicationName("OpenGuard")
        self.setApplicationVersion("0.7.0")

        # Use Fusion style for modern cross-platform appearance
        self.setStyle("Fusion")

        self.main_window: MainWindow | None = None
        self.hardening_manager: HardeningManager | None = None

    def setup_ui(self) -> None:
        """Build the user interface and connect it to the backend.

        Safe to call more than once; the existing window is kept.
        """
        if self.main_window is not None:
            return

        self.hardening_manager = HardeningManager()
        self.main_window = MainWindow()

        self.main_window.toggle_protection_clicked.connect(self._on_toggle_requested)
        self.hardening_manager.status_changed.connect(self.main_window.set_protection_status)

    def _on_toggle_requested(self) -> None:
        """Enable or disable hardening depending on the current state.

        The manager holds the authoritative status, since it reflects what was
        actually applied to the system rather than what the window last drew.
        """
        if self.hardening_manager.is_protected:
            self.hardening_manager.disable_hardening()
        else:
            self.hardening_manager.enable_hardening()

    def run(self) -> int:
        """Show main window and start the event loop.

        Returns:
            int: Exit code from the Qt event loop (0 for normal exit)
        """
        self.setup_ui()
        self.main_window.show()

        return self.exec()
