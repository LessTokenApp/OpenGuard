"""Onboarding wizard for first-run setup."""

from PyQt6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QDialog,
)
from PyQt6.QtCore import pyqtSignal

from src.models.settings import Settings


class OnboardingWizard(QWizard):
    """First-run setup wizard with 4 screens.

    Guides users through initial configuration including protection level
    selection. Emits completed signal with final settings.

    Signals:
        completed: Emitted when wizard completes (accept only, not cancel)
            with the configured Settings object.
    """

    completed = pyqtSignal(Settings)

    def __init__(self) -> None:
        """Initialize the onboarding wizard.

        Sets up 4-page wizard with welcome, protection info, firewall
        selection, and completion screens.
        """
        super().__init__()
        self.setWindowTitle("OpenGuard Setup")
        self.setGeometry(300, 300, 500, 400)

        # Add pages
        self.page1 = self.create_welcome_page()
        self.page2 = self.create_protection_page()
        self.page3 = self.create_firewall_page()
        self.page4 = self.create_complete_page()

        self.addPage(self.page1)
        self.addPage(self.page2)
        self.addPage(self.page3)
        self.addPage(self.page4)

        self.finished.connect(self.on_finished)

    def create_welcome_page(self) -> QWizardPage:
        """Create welcome screen (Screen 1).

        Returns:
            QWizardPage: Welcome page
        """
        page = QWizardPage()
        page.setTitle("Welcome to OpenGuard!")
        layout = QVBoxLayout()

        label = QLabel(
            "🛡️ Stay Safe on Public WiFi\n\nUsing Starbucks WiFi? Airport network?\n"
            "OpenGuard watches for threats & blocks attacks."
        )
        layout.addWidget(label)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def create_protection_page(self) -> QWizardPage:
        """Create protection info screen (Screen 2).

        Returns:
            QWizardPage: Protection info page
        """
        page = QWizardPage()
        page.setTitle("What OpenGuard Protects")
        layout = QVBoxLayout()

        label = QLabel(
            "✅ DNS Spoofing\n"
            "✅ MITM Attacks\n"
            "✅ Network Sniffing\n"
            "✅ Gateway Anomalies\n\n"
            "⚠️  Note: Does NOT encrypt traffic. Use with VPN."
        )
        layout.addWidget(label)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def create_firewall_page(self) -> QWizardPage:
        """Create firewall level selection screen (Screen 3).

        Returns:
            QWizardPage: Firewall level selection page
        """
        page = QWizardPage()
        page.setTitle("Choose Protection Level")
        layout = QVBoxLayout()

        group = QButtonGroup()

        # Basic
        radio_basic = QRadioButton("⭐ Basic (Recommended) - DNS + Web only")
        group.addButton(radio_basic, 0)
        layout.addWidget(radio_basic)

        # Moderate
        radio_moderate = QRadioButton("Moderate - Add Email, SSH, NTP")
        radio_moderate.setChecked(True)
        group.addButton(radio_moderate, 1)
        layout.addWidget(radio_moderate)

        # Relaxed
        radio_relaxed = QRadioButton("Relaxed - Maximum compatibility")
        group.addButton(radio_relaxed, 2)
        layout.addWidget(radio_relaxed)

        layout.addStretch()

        # Store reference for get_settings
        page.button_group = group
        page.setLayout(layout)
        return page

    def create_complete_page(self) -> QWizardPage:
        """Create completion screen (Screen 4).

        Returns:
            QWizardPage: Completion page
        """
        page = QWizardPage()
        page.setTitle("You're All Set!")
        layout = QVBoxLayout()

        label = QLabel(
            "✅ Configuration Complete\n\n"
            "Protection is now ON.\n"
            "Minimize to tray to stay protected."
        )
        layout.addWidget(label)
        layout.addStretch()

        page.setLayout(layout)
        return page

    def get_settings(self) -> Settings:
        """Return configured settings based on wizard selections.

        Returns:
            Settings: Settings object with collected configuration
        """
        # Get firewall level from page 3
        button_group = self.page3.button_group
        checked_id = button_group.checkedId()

        # Map button group IDs to firewall levels
        firewall_level_map = {
            0: "Basic",
            1: "Moderate",
            2: "Relaxed",
        }
        firewall = firewall_level_map.get(checked_id, "Moderate")

        return Settings(firewall_level=firewall)

    def on_finished(self, result: int) -> None:
        """Handle wizard completion and emit completed signal.

        Called when wizard finishes (accept or reject). Only emits the
        completed signal if the wizard was accepted (not cancelled).

        Args:
            result: Dialog result code from QWizard.finished signal
                   (QDialog.DialogCode.Accepted = 1, .Rejected = 0)
        """
        if result == QDialog.DialogCode.Accepted:
            settings = self.get_settings()
            self.completed.emit(settings)
