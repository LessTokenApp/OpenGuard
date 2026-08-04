"""OpenGuard main application class."""

import sys

from PyQt6.QtWidgets import QApplication


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

        # Placeholder for main window (will be set by main_window module in task 3)
        self.main_window = None

    def run(self) -> int:
        """Show main window and start the event loop.

        Returns:
            int: Exit code from the Qt event loop (0 for normal exit)
        """
        if self.main_window:
            self.main_window.show()

        return self.exec()
