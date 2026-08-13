"""Settings dialog with tabbed interface for configuration."""

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.settings import Settings
from src.ui.styles import get_stylesheet


class SettingsDialog(QDialog):
    """Settings configuration window.

    Displays a tabbed interface with three tabs:
    - Protection: Firewall level, DNS provider, and security options
    - Analytics: Event logging and data retention settings
    - Appearance: UI preferences and startup options

    Signals:
        settings_changed: Emitted when settings are modified
    """

    settings_changed = pyqtSignal()

    def __init__(self, initial_settings: Optional[Settings] = None) -> None:
        """Initialize the settings dialog.

        Args:
            initial_settings: Optional Settings object to populate the dialog with.
                            If None, uses Settings defaults.
        """
        super().__init__()
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 500, 400)
        self.setStyleSheet(get_stylesheet(dark_mode=True))

        if initial_settings is None:
            self.settings = Settings()
        else:
            self.settings = initial_settings

        layout = QVBoxLayout()

        # TAB WIDGET
        self.tabs = QTabWidget()

        # Tab 1: Protection
        protection_tab = self._create_protection_tab()
        self.tabs.addTab(protection_tab, "🛡️  Protection")

        # Tab 2: Analytics
        analytics_tab = self._create_analytics_tab()
        self.tabs.addTab(analytics_tab, "📊 Analytics")

        # Tab 3: Appearance
        appearance_tab = self._create_appearance_tab()
        self.tabs.addTab(appearance_tab, "🎨 Appearance")

        layout.addWidget(self.tabs)

        # BUTTONS
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _on_save_clicked(self) -> None:
        """Handle save button click.

        Emits settings_changed signal and closes the dialog.
        """
        self.settings_changed.emit()
        self.accept()

    def _create_protection_tab(self) -> QWidget:
        """Create protection settings tab.

        Contains:
        - Firewall level selection
        - DNS provider selection
        - DNS security toggle
        - Network monitoring toggle

        Returns:
            QWidget: The protection tab widget
        """
        widget = QWidget()
        v_layout = QVBoxLayout()

        # Firewall Level
        v_layout.addWidget(QLabel("Firewall Level:"))
        self.firewall_combo = QComboBox()
        self.firewall_combo.addItems(["Basic", "Moderate", "Relaxed"])
        self.firewall_combo.setCurrentText(self.settings.firewall_level)
        v_layout.addWidget(self.firewall_combo)

        v_layout.addSpacing(10)

        # DNS Provider
        v_layout.addWidget(QLabel("DNS Provider:"))
        self.dns_combo = QComboBox()
        self.dns_combo.addItems(["Cloudflare", "Google", "Quad9", "OpenDNS"])
        self.dns_combo.setCurrentText(self.settings.dns_provider)
        v_layout.addWidget(self.dns_combo)

        # DNS Enabled
        self.dns_enabled_check = QCheckBox("Enable DNS Security")
        self.dns_enabled_check.setChecked(self.settings.dns_enabled)
        v_layout.addWidget(self.dns_enabled_check)

        # Network Monitoring
        self.network_monitoring_check = QCheckBox("Monitor Gateway MAC")
        self.network_monitoring_check.setChecked(self.settings.network_monitoring)
        v_layout.addWidget(self.network_monitoring_check)

        v_layout.addStretch()
        widget.setLayout(v_layout)
        return widget

    def _create_analytics_tab(self) -> QWidget:
        """Create analytics settings tab.

        Contains:
        - Analytics toggle
        - Retention days spinner

        Returns:
            QWidget: The analytics tab widget
        """
        widget = QWidget()
        v_layout = QVBoxLayout()

        self.analytics_enabled_check = QCheckBox("Auto-log events")
        self.analytics_enabled_check.setChecked(self.settings.analytics_enabled)
        v_layout.addWidget(self.analytics_enabled_check)

        v_layout.addWidget(QLabel("Retention (days):"))
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(7, 365)
        self.retention_spin.setValue(self.settings.retention_days)
        v_layout.addWidget(self.retention_spin)

        v_layout.addStretch()
        widget.setLayout(v_layout)
        return widget

    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab.

        Contains:
        - Dark mode toggle
        - Auto-start toggle
        - System tray toggle
        - Daily tips toggle

        Returns:
            QWidget: The appearance tab widget
        """
        widget = QWidget()
        v_layout = QVBoxLayout()

        self.dark_mode_check = QCheckBox("Dark Mode")
        self.dark_mode_check.setChecked(self.settings.dark_mode)
        v_layout.addWidget(self.dark_mode_check)

        self.auto_start_check = QCheckBox("Auto-start on login")
        self.auto_start_check.setChecked(self.settings.auto_start)
        v_layout.addWidget(self.auto_start_check)

        self.systray_check = QCheckBox("System tray integration")
        self.systray_check.setChecked(self.settings.systray_enabled)
        v_layout.addWidget(self.systray_check)

        self.tips_check = QCheckBox("Show daily tips")
        self.tips_check.setChecked(self.settings.show_daily_tips)
        v_layout.addWidget(self.tips_check)

        v_layout.addStretch()
        widget.setLayout(v_layout)
        return widget

    def get_settings(self) -> Settings:
        """Return current settings.

        Retrieves the current state of all settings controls and returns
        them as a Settings dataclass instance.

        Returns:
            Settings: A Settings object with current configuration values
        """
        return Settings(
            firewall_level=self.firewall_combo.currentText(),
            dns_provider=self.dns_combo.currentText(),
            dns_enabled=self.dns_enabled_check.isChecked(),
            network_monitoring=self.network_monitoring_check.isChecked(),
            auto_start=self.auto_start_check.isChecked(),
            dark_mode=self.dark_mode_check.isChecked(),
            systray_enabled=self.systray_check.isChecked(),
            analytics_enabled=self.analytics_enabled_check.isChecked(),
            retention_days=self.retention_spin.value(),
            show_daily_tips=self.tips_check.isChecked(),
        )

    def set_firewall_level(self, level: str) -> None:
        """Set firewall level (for testing).

        Args:
            level: One of "Basic", "Moderate", or "Relaxed"

        Raises:
            ValueError: If level is not a valid firewall level
        """
        if level not in ["Basic", "Moderate", "Relaxed"]:
            raise ValueError(
                f"Invalid firewall level: {level}. " f"Must be one of: Basic, Moderate, Relaxed"
            )
        self.firewall_combo.setCurrentText(level)
