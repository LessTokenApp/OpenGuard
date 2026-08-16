"""Main application window with status card and activity log."""

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.models.event import Event
from src.ui.styles import COLOR_WARN, get_stylesheet


class MainWindow(QMainWindow):
    """Main window for OpenGuard application.

    Displays:
    - Status card showing protection status
    - Toggle protection button
    - Activity log with recent events

    Signals:
        toggle_protection_clicked: Emitted when toggle button is clicked
    """

    toggle_protection_clicked = pyqtSignal()

    def __init__(self) -> None:
        """Initialize the main window.

        Sets up:
        - Window title and size
        - Status card with protection indicator
        - Toggle protection button
        - Persistent disclaimer label
        - Activity log for recent events
        """
        super().__init__()

        self.setWindowTitle("OpenGuard")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(get_stylesheet(dark_mode=True))

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create status card layout
        status_layout = QHBoxLayout()

        # Status indicator
        self.status_label = QTextEdit()
        self.status_label.setReadOnly(True)
        self.status_label.setMaximumHeight(60)
        self.status_label.setPlainText("🟢 PROTECTED")
        status_layout.addWidget(self.status_label)

        # Toggle button
        self.toggle_button = QPushButton("Disable Protection")
        self.toggle_button.clicked.connect(self._on_toggle_clicked)
        status_layout.addWidget(self.toggle_button)

        main_layout.addLayout(status_layout)

        # Persistent disclaimer label
        self.disclaimer_label = QLabel()
        self.disclaimer_label.setStyleSheet(f"color: {COLOR_WARN};")
        self.disclaimer_label.setText(
            "Uyarı: OpenGuard trafiği şifrelemez ve VPN ya da antivirüs yerine geçmez."
        )
        self.disclaimer_label.setWordWrap(True)
        main_layout.addWidget(self.disclaimer_label)

        # Activity log
        activity_label = QTextEdit()
        activity_label.setReadOnly(True)
        activity_label.setMaximumHeight(30)
        activity_label.setPlainText("Activity Log:")
        main_layout.addWidget(activity_label)

        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        main_layout.addWidget(self.activity_log)

        self.is_protected = True

    def set_protection_status(self, is_protected: bool) -> None:
        """Set the protection status and update UI.

        Args:
            is_protected: True if system is protected, False otherwise
        """
        self.is_protected = is_protected
        if is_protected:
            self.status_label.setPlainText("🟢 PROTECTED")
            self.toggle_button.setText("Disable Protection")
        else:
            self.status_label.setPlainText("🔴 UNPROTECTED")
            self.toggle_button.setText("Enable Protection")

    def add_activity_log_entry(self, event: Event) -> None:
        """Add an event to the activity log.

        The event is colored by severity:
        - SUCCESS: Green
        - WARN: Orange
        - ERROR: Red

        Args:
            event: Event object to add to the log
        """
        timestamp_str = event.timestamp.strftime("%H:%M:%S")
        category_str = f"[{event.category}] " if event.category else ""
        log_entry = f"{timestamp_str} {category_str}{event.event}\n"

        # Get current text and prepend new entry
        current_text = self.activity_log.toPlainText()
        new_text = log_entry + current_text

        # Limit to last 100 entries to prevent memory issues
        lines = new_text.split("\n")
        if len(lines) > 100:
            new_text = "\n".join(lines[:100])

        self.activity_log.setPlainText(new_text)

        # Apply color formatting based on severity
        self._apply_severity_color(event.severity)

    def get_toggle_button(self) -> QPushButton:
        """Get the toggle protection button.

        Returns:
            QPushButton: The toggle protection button
        """
        return self.toggle_button

    def _on_toggle_clicked(self) -> None:
        """Handle toggle button click event.

        Emits the toggle_protection_clicked signal.
        """
        self.toggle_protection_clicked.emit()

    def _apply_severity_color(self, severity: str) -> None:
        """Apply color formatting to activity log based on severity.

        Args:
            severity: Event severity ("SUCCESS", "WARN", "ERROR")
        """
        # Get the text edit's underlying document
        document = self.activity_log.document()

        # Color mapping for severity levels
        # Note: For now, we'll use setStyleSheet to apply colors
        # This is a simple implementation; a more advanced version
        # might use QTextCursor and QTextFormat for per-line coloring
        if severity == "SUCCESS":
            # Green text for success
            self.activity_log.setStyleSheet("color: green;")
        elif severity == "WARN":
            # Orange/yellow text for warnings
            self.activity_log.setStyleSheet("color: orange;")
        elif severity == "ERROR":
            # Red text for errors
            self.activity_log.setStyleSheet("color: red;")
        else:
            # Default text color
            self.activity_log.setStyleSheet("")
