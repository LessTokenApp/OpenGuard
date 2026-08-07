"""System tray integration for OpenGuard application."""

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


class SystemTray(QSystemTrayIcon):
    """System tray icon with context menu for OpenGuard.

    Displays:
    - Protection status (green/red/yellow icon)
    - Context menu with status, toggle, settings, help, and exit options
    - Tooltip showing protection status and last activity

    Signals:
        toggle_clicked: Emitted when toggle protection action is selected
        settings_clicked: Emitted when settings action is selected
        exit_clicked: Emitted when exit action is selected
    """

    toggle_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()

    def __init__(self) -> None:
        """Initialize the system tray icon.

        Sets up:
        - Tray icon with protected status (green)
        - Context menu with all required actions
        - Tooltip showing status and activity
        """
        super().__init__()

        self.is_protected = True
        self.last_activity = datetime.now()

        # Create context menu
        self.tray_menu = QMenu()
        self._setup_menu()

        # Set the menu
        self.setContextMenu(self.tray_menu)

        # Set initial icon and tooltip
        self._update_icon()
        self._update_tooltip()

    def set_protection_status(self, is_protected: bool) -> None:
        """Set the protection status and update UI.

        Args:
            is_protected: True if system is protected, False otherwise
        """
        self.is_protected = is_protected
        self.last_activity = datetime.now()
        self._update_icon()
        self._update_tooltip()
        self._update_menu()

    def _setup_menu(self) -> None:
        """Set up the context menu with all required actions."""
        # Status indicator (read-only)
        self.status_action = self.tray_menu.addAction("🟢 Protected")
        self.status_action.setEnabled(False)

        # Separator
        self.tray_menu.addSeparator()

        # Toggle protection action
        self.toggle_action = self.tray_menu.addAction("🔴 Disable (5 min)")
        self.toggle_action.triggered.connect(self._on_toggle_clicked)

        # Separator
        self.tray_menu.addSeparator()

        # Settings action
        self.settings_action = self.tray_menu.addAction("⚙️ Settings")
        self.settings_action.triggered.connect(self._on_settings_clicked)

        # Analytics action
        self.analytics_action = self.tray_menu.addAction("📊 Analytics")
        self.analytics_action.triggered.connect(self._on_analytics_clicked)

        # Help action
        self.help_action = self.tray_menu.addAction("? Help")
        self.help_action.triggered.connect(self._on_help_clicked)

        # Separator
        self.tray_menu.addSeparator()

        # Exit action
        self.exit_action = self.tray_menu.addAction("✖️ Exit")
        self.exit_action.triggered.connect(self._on_exit_clicked)

    def _update_menu(self) -> None:
        """Update menu items based on current protection status."""
        if self.is_protected:
            self.status_action.setText("🟢 Protected")
            self.toggle_action.setText("🔴 Disable (5 min)")
        else:
            self.status_action.setText("🔴 Unprotected")
            self.toggle_action.setText("🟢 Enable")

    def _update_icon(self) -> None:
        """Update the tray icon based on protection status.

        Icon states:
        - 🟢 Green: Protected
        - 🔴 Red: Unprotected
        - 🟡 Yellow: Warning (reserved for future use)
        """
        icon = self._create_icon()
        self.setIcon(icon)

    def _create_icon(self) -> QIcon:
        """Create a tray icon with appropriate color.

        Returns:
            QIcon: Icon with color based on protection status
        """
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        # Determine color based on status
        if self.is_protected:
            color = QColor("green")
        else:
            color = QColor("red")

        # Draw a circle with the appropriate color
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(8, 8, 48, 48)
        painter.end()

        return QIcon(pixmap)

    def _update_tooltip(self) -> None:
        """Update the tooltip with status and last activity."""
        if self.is_protected:
            status = "Protected"
        else:
            status = "Unprotected"

        activity_time = self.last_activity.strftime("%H:%M:%S")
        tooltip = f"OpenGuard: {status} | Last activity: {activity_time}"
        self.setToolTip(tooltip)

    def _on_toggle_clicked(self) -> None:
        """Handle toggle protection action.

        Emits the toggle_clicked signal.
        """
        self.toggle_clicked.emit()

    def _on_settings_clicked(self) -> None:
        """Handle settings action.

        Emits the settings_clicked signal.
        """
        self.settings_clicked.emit()

    def _on_analytics_clicked(self) -> None:
        """Handle analytics action.

        Reserved for future implementation.
        """
        # Future implementation: open analytics window
        pass

    def _on_help_clicked(self) -> None:
        """Handle help action.

        Reserved for future implementation.
        """
        # Future implementation: show help dialog or documentation
        pass

    def _on_exit_clicked(self) -> None:
        """Handle exit action.

        Emits the exit_clicked signal.
        """
        self.exit_clicked.emit()
