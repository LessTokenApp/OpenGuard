"""Analytics Modal for displaying event statistics and PRO features."""

from datetime import datetime
from typing import List

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

from src.models.event import Event
from src.ui.styles import get_stylesheet


class AnalyticsModal(QDialog):
    """Analytics viewer - FREE basic / PRO advanced"""

    def __init__(self, is_pro: bool = False):
        super().__init__()
        self.setWindowTitle("Analytics Dashboard")
        self.setGeometry(200, 200, 600, 500)
        self.setStyleSheet(get_stylesheet(dark_mode=True))
        self.is_pro = is_pro

        layout = QVBoxLayout()

        # Title
        title = QLabel(f"📊 Analytics {'(PRO)' if is_pro else '(Basic)'}")
        layout.addWidget(title)

        # Statistics
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        # Email alerts (PRO only)
        self.email_alerts_label = QLabel()
        if not is_pro:
            self.email_alerts_label.setText("📧 Email Alerts — PRO Feature [Upgrade]")
        else:
            self.email_alerts_label.setText("📧 Email alerts enabled")
        layout.addWidget(self.email_alerts_label)

        layout.addStretch()

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)
        self.events: List[Event] = []

    def set_events(self, events: List[Event]) -> None:
        """Update analytics from events list"""
        self.events = events
        self._update_display()

    def _update_display(self) -> None:
        """Refresh display based on events"""
        total = len(self.events)
        # Exclude system/administrative events from threat count
        threat_count = sum(
            1 for e in self.events
            if e.severity in ["WARN", "ERROR"] and e.category != "system"
        )

        # Calculate 24h risk, also excluding system events
        last_24h = [
            e for e in self.events if (datetime.now() - e.timestamp).total_seconds() < 86400
        ]
        risk_24h_count = sum(
            1 for e in last_24h
            if e.severity in ["WARN", "ERROR"] and e.category != "system"
        )

        if risk_24h_count == 0:
            risk_status = "LOW"
        elif risk_24h_count <= 2:
            risk_status = "MEDIUM"
        else:
            risk_status = "HIGH"

        stats_text = (
            f"Total Events: {total}\n"
            f"Threats Blocked: {threat_count}\n"
            f"Last 24h Risk: {risk_status}"
        )

        if self.is_pro:
            stats_text += "\n📈 7-Day Trends: Available [Graph]"

        self.stats_label.setText(stats_text)
