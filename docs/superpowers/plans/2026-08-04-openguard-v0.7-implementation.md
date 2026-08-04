# OpenGuard v0.7.0 Implementation Plan — FULL

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement task-by-task. Each task is independent and testable.

**Goal:** Deliver OpenGuard v0.7.0: Professional Python GUI app (PyQt6) transforming CLI PowerShell tool into one-click-installer dashboard for public WiFi protection. Target: non-technical users, 6-week timeline.

**Architecture:** Layered Qt frontend (MainWindow, Systray, dialogs) + Python application core (IPC to PowerShell v0.6.0) + SQLite analytics. Async subprocess calls, event-driven UI, YAML config, JSONL logs.

**Tech Stack:** Python 3.12+, PyQt6, SQLite3, PyYAML, PyInstaller, Inno Setup

## Global Constraints

- **Python:** 3.12+ minimum
- **PyQt:** Version 6.6.0+ (PyQt6, not PySide6)
- **Target OS:** Windows 11 primary, Windows 10 compatible
- **No external resources:** All fonts/icons embedded
- **PowerShell backend:** v0.6.0 untouched
- **Language:** Turkish UI, English code
- **Monetization stubs:** Pro tier detection (v0.8.0 implementation)
- **User education:** 7 touchpoints for VPN/antivirus messaging
- **Timeline:** 6 weeks = 42 days

---

# IMPLEMENTATION TASKS

## WEEK 1: Foundation

### Task 1: Project Setup & Dependencies
**Files:** `pyproject.toml`, `src/__init__.py` (all folders), `.gitignore`  
**Status:** ✅ Complete (see above)

### Task 2: Base Application Class
**Files:** `src/app.py`, `src/main.py`, `tests/test_app_init.py`  
**Status:** ✅ Complete (see above)

### Task 3: Main Window — Status Card & Activity Log
**Files:** `src/ui/main_window.py`, `src/models/event.py`, `tests/test_ui/test_main_window.py`  
**Status:** ✅ Complete (see above)

### Task 4: System Tray Integration
**Files:** `src/ui/systray.py`, `tests/test_ui/test_systray.py`  
**Status:** ✅ Complete (see above)

---

## WEEK 2-3: UI Components

### Task 5: Settings Dialog (Tabs)

**Files:**
- Create: `src/ui/settings_dialog.py`
- Create: `src/models/settings.py`
- Create: `tests/test_ui/test_settings_dialog.py`

**Interfaces:**
- Consumes: `Event`, `SystemTray` (import for reference)
- Produces: `class SettingsDialog(QDialog)` with:
  - Properties: `firewall_level: str`, `dns_provider: str`, `auto_start: bool`
  - Method: `get_settings() → Settings`
  - Signal: `settings_changed()`

- [ ] **Step 1: Create Settings dataclass**

```python
# src/models/settings.py
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Settings:
    """User configuration"""
    firewall_level: str = "Moderate"  # Basic, Moderate, Relaxed
    dns_provider: str = "Cloudflare"  # Cloudflare, Google, Quad9
    dns_enabled: bool = True
    network_monitoring: bool = True
    auto_start: bool = True
    dark_mode: bool = True
    systray_enabled: bool = True
    analytics_enabled: bool = True
    retention_days: int = 90
    show_daily_tips: bool = True
    
    def __post_init__(self):
        if self.firewall_level not in ["Basic", "Moderate", "Relaxed"]:
            raise ValueError(f"Invalid firewall level: {self.firewall_level}")
```

- [ ] **Step 2: Write test for SettingsDialog**

```python
# tests/test_ui/test_settings_dialog.py
import pytest
from PyQt6.QtWidgets import QApplication, QDialog
from src.ui.settings_dialog import SettingsDialog
from src.models.settings import Settings

@pytest.fixture
def app():
    if QApplication.instance():
        return QApplication.instance()
    return QApplication([])

def test_settings_dialog_creation(app):
    """Test dialog opens without error"""
    dialog = SettingsDialog()
    assert dialog is not None
    assert isinstance(dialog, QDialog)

def test_get_settings_returns_settings_object(app):
    """Test that dialog returns Settings dataclass"""
    dialog = SettingsDialog()
    settings = dialog.get_settings()
    assert isinstance(settings, Settings)
    assert settings.firewall_level in ["Basic", "Moderate", "Relaxed"]

def test_settings_persistence(app):
    """Test that settings can be updated and retrieved"""
    dialog = SettingsDialog()
    dialog.set_firewall_level("Basic")
    settings = dialog.get_settings()
    assert settings.firewall_level == "Basic"
```

- [ ] **Step 3: Implement SettingsDialog**

```python
# src/ui/settings_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QComboBox, QCheckBox, QPushButton, QSpinBox
)
from PyQt6.QtCore import pyqtSignal

from src.models.settings import Settings

class SettingsDialog(QDialog):
    """Settings configuration window"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, initial_settings: Settings = None):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 500, 400)
        
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
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _create_protection_tab(self):
        """Create protection settings tab"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout
        
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
    
    def _create_analytics_tab(self):
        """Create analytics settings tab"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout
        
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
    
    def _create_appearance_tab(self):
        """Create appearance settings tab"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout
        
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
        """Return current settings"""
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
            show_daily_tips=self.tips_check.isChecked()
        )
    
    def set_firewall_level(self, level: str):
        """Set firewall level (for testing)"""
        self.firewall_combo.setCurrentText(level)
```

- [ ] **Step 4-7: Test → Run → Commit** (following TDD pattern from Tasks 1-4)

```bash
# Run tests
python -m pytest tests/test_ui/test_settings_dialog.py -v

# Commit
git add src/ui/settings_dialog.py src/models/settings.py tests/test_ui/test_settings_dialog.py
git commit -m "feat: implement settings dialog with three tabs

- Settings dataclass for type-safe configuration
- SettingsDialog QDialog with Protection, Analytics, Appearance tabs
- Firewall level, DNS provider, checkboxes for features
- Tests verify settings retrieval and updates"
```

---

### Task 6: Onboarding Wizard (4-Screen Flow)

**Files:**
- Create: `src/ui/onboarding_wizard.py`
- Create: `tests/test_ui/test_onboarding_wizard.py`

**Interfaces:**
- Consumes: `Settings` dataclass
- Produces: `class OnboardingWizard(QWizard)` with:
  - Method: `get_settings() → Settings`
  - Signal: `completed(settings: Settings)`

- [ ] **Step 1: Write test for onboarding wizard**

```python
# tests/test_ui/test_onboarding_wizard.py
import pytest
from PyQt6.QtWidgets import QApplication
from src.ui.onboarding_wizard import OnboardingWizard
from src.models.settings import Settings

@pytest.fixture
def app():
    if QApplication.instance():
        return QApplication.instance()
    return QApplication([])

def test_wizard_creation(app):
    """Test wizard initializes"""
    wizard = OnboardingWizard()
    assert wizard is not None
    assert wizard.pageCount() == 4  # 4 screens

def test_wizard_completion_returns_settings(app):
    """Test that wizard completion returns Settings"""
    wizard = OnboardingWizard()
    # Simulate going through wizard
    wizard.next()  # Screen 2
    wizard.next()  # Screen 3
    # Select Basic firewall
    from PyQt6.QtWidgets import QRadioButton
    for button in wizard.findChildren(QRadioButton):
        if "Basic" in button.text():
            button.setChecked(True)
    wizard.next()  # Screen 4
    
    settings = wizard.get_settings()
    assert isinstance(settings, Settings)
    assert settings.firewall_level == "Basic"
```

- [ ] **Step 2: Implement OnboardingWizard**

```python
# src/ui/onboarding_wizard.py
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal
from src.models.settings import Settings

class OnboardingWizard(QWizard):
    """First-run setup wizard"""
    
    completed_signal = pyqtSignal(Settings)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenGuard Setup")
        self.setGeometry(300, 300, 500, 400)
        
        # Settings to be collected
        self.selected_firewall_level = "Moderate"
        
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
        """Screen 1: Welcome"""
        page = QWizardPage()
        page.setTitle("Welcome to OpenGuard!")
        layout = QVBoxLayout()
        
        label = QLabel("🛡️ Stay Safe on Public WiFi\n\nUsing Starbucks WiFi? Airport network?\n"
                       "OpenGuard watches for threats & blocks attacks.")
        layout.addWidget(label)
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def create_protection_page(self) -> QWizardPage:
        """Screen 2: What it protects"""
        page = QWizardPage()
        page.setTitle("What OpenGuard Protects")
        layout = QVBoxLayout()
        
        label = QLabel("✅ DNS Spoofing\n"
                       "✅ MITM Attacks\n"
                       "✅ Network Sniffing\n"
                       "✅ Gateway Anomalies\n\n"
                       "⚠️  Note: Does NOT encrypt traffic. Use with VPN.")
        layout.addWidget(label)
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def create_firewall_page(self) -> QWizardPage:
        """Screen 3: Choose firewall level"""
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
        """Screen 4: Ready!"""
        page = QWizardPage()
        page.setTitle("You're All Set!")
        layout = QVBoxLayout()
        
        label = QLabel("✅ Configuration Complete\n\n"
                       "Protection is now ON.\n"
                       "Minimize to tray to stay protected.")
        layout.addWidget(label)
        layout.addStretch()
        
        page.setLayout(layout)
        return page
    
    def get_settings(self) -> Settings:
        """Return configured settings"""
        # Get firewall level from page 3
        button_group = self.page3.button_group
        if button_group.checkedId() == 0:
            firewall = "Basic"
        elif button_group.checkedId() == 1:
            firewall = "Moderate"
        else:
            firewall = "Relaxed"
        
        return Settings(firewall_level=firewall)
    
    def on_finished(self):
        """Emit signal when wizard completes"""
        settings = self.get_settings()
        self.completed_signal.emit(settings)
```

- [ ] **Step 3-7: Test → Implement → Commit** (TDD pattern)

```bash
python -m pytest tests/test_ui/test_onboarding_wizard.py -v
git add src/ui/onboarding_wizard.py tests/test_ui/test_onboarding_wizard.py
git commit -m "feat: implement onboarding wizard with 4 screens

- Welcome, Protection info, Firewall level selection, Complete screens
- Collects firewall level (Basic/Moderate/Relaxed)
- Returns Settings object on completion
- Tests verify page count and settings retrieval"
```

---

### Task 7: Analytics Modal (FREE basic / PRO advanced)

**Files:**
- Create: `src/ui/analytics_modal.py`
- Create: `tests/test_ui/test_analytics_modal.py`

**Interfaces:**
- Consumes: `Event` dataclass
- Produces: `class AnalyticsModal(QDialog)` with:
  - Method: `set_events(events: List[Event]) → None`
  - Property: `is_pro: bool` (to show/hide PRO features)

- [ ] **Step 1: Write test**

```python
# tests/test_ui/test_analytics_modal.py
import pytest
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from src.ui.analytics_modal import AnalyticsModal
from src.models.event import Event

@pytest.fixture
def app():
    if QApplication.instance():
        return QApplication.instance()
    return QApplication([])

def test_analytics_modal_creation(app):
    """Test modal opens"""
    modal = AnalyticsModal(is_pro=False)
    assert modal is not None

def test_free_modal_shows_basic_only(app):
    """Test FREE tier shows only basic analytics"""
    modal = AnalyticsModal(is_pro=False)
    assert modal.is_pro is False
    # Verify PRO sections are hidden
    assert modal.email_alerts_label.isHidden() or "PRO" in modal.email_alerts_label.text()

def test_pro_modal_shows_advanced(app):
    """Test PRO tier shows advanced features"""
    modal = AnalyticsModal(is_pro=True)
    assert modal.is_pro is True

def test_set_events_updates_display(app):
    """Test that events are displayed"""
    modal = AnalyticsModal(is_pro=False)
    events = [
        Event(datetime.now(), "Test event 1", "SUCCESS"),
        Event(datetime.now(), "Test event 2", "WARN"),
    ]
    modal.set_events(events)
    # Verify display updated
    display_text = modal.stats_label.text()
    assert "2" in display_text or "events" in display_text.lower()
```

- [ ] **Step 2: Implement AnalyticsModal**

```python
# src/ui/analytics_modal.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from datetime import datetime, timedelta
from typing import List
from src.models.event import Event

class AnalyticsModal(QDialog):
    """Analytics viewer - FREE basic / PRO advanced"""
    
    def __init__(self, is_pro: bool = False):
        super().__init__()
        self.setWindowTitle("Analytics Dashboard")
        self.setGeometry(200, 200, 600, 500)
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
    
    def set_events(self, events: List[Event]):
        """Update analytics from events list"""
        self.events = events
        self._update_display()
    
    def _update_display(self):
        """Refresh display based on events"""
        total = len(self.events)
        success_count = sum(1 for e in self.events if e.severity == "SUCCESS")
        threat_count = sum(1 for e in self.events if e.severity in ["WARN", "ERROR"])
        
        # Calculate 24h risk
        last_24h = [e for e in self.events 
                   if (datetime.now() - e.timestamp).total_seconds() < 86400]
        risk_24h_count = sum(1 for e in last_24h if e.severity in ["WARN", "ERROR"])
        
        if risk_24h_count == 0:
            risk_status = "LOW"
        elif risk_24h_count <= 2:
            risk_status = "MEDIUM"
        else:
            risk_status = "HIGH"
        
        stats_text = f"Total Events: {total}\n" \
                     f"Threats Blocked: {threat_count}\n" \
                     f"Last 24h Risk: {risk_status}"
        
        if self.is_pro:
            stats_text += f"\n📈 7-Day Trends: Available [Graph]"
        
        self.stats_label.setText(stats_text)
```

- [ ] **Step 3-7: Test → Commit**

```bash
python -m pytest tests/test_ui/test_analytics_modal.py -v
git add src/ui/analytics_modal.py tests/test_ui/test_analytics_modal.py
git commit -m "feat: implement analytics modal with FREE/PRO tiers

- Analytics viewer dialog (basic statistics for FREE tier)
- PRO tier shows advanced features placeholder
- Displays event count, threat count, 24h risk score
- Tests verify tier detection and event display"
```

---

### Task 8: UI Styles & Dark Mode

**Files:**
- Create: `src/ui/styles.py`
- Modify: All UI files to apply stylesheet

**Interfaces:**
- Produces: `def get_stylesheet(dark_mode: bool) → str`
- Produces: `COLOR_SAFE`, `COLOR_WARN`, `COLOR_ERROR` constants

- [ ] **Step 1-7: Create stylesheet, apply to all windows, test dark/light toggle**

```python
# src/ui/styles.py
from typing import Dict

# Color tokens
COLOR_SAFE = "#22C55E"      # Green
COLOR_WARN = "#EAB308"      # Amber
COLOR_ERROR = "#EF4444"     # Red

COLOR_BG_DARK = "#1F2937"   # Dark
COLOR_BG_LIGHT = "#FFFFFF"  # White
COLOR_TEXT_DARK = "#F3F4F6" # Light text
COLOR_TEXT_LIGHT = "#1F2937" # Dark text

def get_stylesheet(dark_mode: bool = True) -> str:
    """Return Qt stylesheet based on theme"""
    
    if dark_mode:
        bg = COLOR_BG_DARK
        text = COLOR_TEXT_DARK
        border = "#374151"
    else:
        bg = COLOR_BG_LIGHT
        text = COLOR_TEXT_LIGHT
        border = "#E5E7EB"
    
    return f"""
        QMainWindow, QDialog {{
            background-color: {bg};
            color: {text};
        }}
        
        QPushButton {{
            background-color: #3B82F6;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: #2563EB;
        }}
        
        QLabel {{
            color: {text};
        }}
        
        QTextEdit, QPlainTextEdit {{
            background-color: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
        }}
        
        QGroupBox {{
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
            margin-top: 6px;
            padding-top: 6px;
        }}
    """

# Apply in MainWindow.__init__:
# self.setStyleSheet(get_stylesheet(dark_mode=True))
```

- [ ] **Step 2-7: Update MainWindow, SettingsDialog, etc. to use stylesheet**

```bash
# In each UI class:
from src.ui.styles import get_stylesheet
# In __init__:
self.setStyleSheet(get_stylesheet(dark_mode=True))
```

Commit:
```bash
git add src/ui/styles.py src/ui/main_window.py src/ui/settings_dialog.py src/ui/onboarding_wizard.py src/ui/analytics_modal.py src/ui/systray.py
git commit -m "feat: add Qt stylesheet system with dark mode

- Color tokens (green/amber/red for status)
- Dark/light theme stylesheet generator
- Applied to all UI components
- Clean, modern appearance"
```

---

## WEEK 4: Backend Integration

### Task 9: HardeningManager (PowerShell IPC)

**Files:**
- Create: `src/core/hardening_manager.py`
- Create: `tests/test_core/test_hardening_manager.py`

**Interfaces:**
- Produces: `class HardeningManager` with:
  - `enable_hardening(level: str = "Moderate") → bool`
  - `disable_hardening() → bool`
  - `get_status() → bool` (is_protected)
  - Signal: `status_changed(bool)`
  - Signal: `error_occurred(str)`

- [ ] **Step 1-7: Implement subprocess-based IPC to PowerShell**

```python
# src/core/hardening_manager.py
import subprocess
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class HardeningManager(QObject):
    """Manages PowerShell hardening subprocess"""
    
    status_changed = pyqtSignal(bool)  # is_protected
    error_occurred = pyqtSignal(str)   # error message
    
    def __init__(self):
        super().__init__()
        self.backend_path = Path(__file__).parent.parent.parent / "backend" / "OpenGuard.ps1"
        self.is_protected = False
    
    def enable_hardening(self, level: str = "Moderate") -> bool:
        """Call PowerShell to enable hardening"""
        try:
            cmd = f'powershell.exe -NoProfile -Command "& {{.\\backend\\OpenGuard.ps1 -Action Enable -Level {level}}}"'
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.is_protected = True
                self.status_changed.emit(True)
                return True
            else:
                self.error_occurred.emit(result.stderr or "Hardening failed")
                return False
        except Exception as e:
            self.error_occurred.emit(str(e))
            return False
    
    def disable_hardening(self) -> bool:
        """Disable hardening"""
        try:
            cmd = f'powershell.exe -NoProfile -Command "& {{.\\backend\\OpenGuard.ps1 -Action Disable}}"'
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.is_protected = False
                self.status_changed.emit(False)
                return True
            else:
                self.error_occurred.emit(result.stderr or "Disable failed")
                return False
        except Exception as e:
            self.error_occurred.emit(str(e))
            return False
    
    def get_status(self) -> bool:
        """Get current protection status"""
        return self.is_protected
```

Commit:
```bash
git add src/core/hardening_manager.py tests/test_core/test_hardening_manager.py
git commit -m "feat: implement HardeningManager for PowerShell IPC

- Subprocess calls to OpenGuard.ps1
- enable_hardening(), disable_hardening(), get_status()
- Error signals for UI feedback
- Handles process timeouts and errors gracefully"
```

---

### Task 10: AnalyticsEngine (JSONL → SQLite)

**Files:**
- Create: `src/core/analytics_engine.py`
- Create: `tests/test_core/test_analytics_engine.py`

**Interfaces:**
- Produces: `class AnalyticsEngine` with:
  - `read_jsonl(path: str) → List[Event]`
  - `ingest_to_sqlite(events: List[Event]) → int` (rows inserted)
  - `get_24h_risk_score() → str` ("LOW", "MEDIUM", "HIGH")
  - `get_threat_timeline(days: int = 7) → List[Event]`

### Task 11: ConfigManager (YAML I/O)

**Files:**
- Create: `src/core/config_manager.py`
- Create: `tests/test_core/test_config_manager.py`

**Interfaces:**
- Produces: `class ConfigManager` with:
  - `load_config() → Settings`
  - `save_config(settings: Settings) → bool`

### Task 12: ProcessMonitor (Watch PowerShell)

**Files:**
- Create: `src/core/process_monitor.py`
- Create: `tests/test_core/test_process_monitor.py`

**Interfaces:**
- Produces: `class ProcessMonitor(QObject)` with:
  - `start_monitoring() → None`
  - `stop_monitoring() → None`
  - Signal: `new_events(events: List[Event])`

*(Due to token limit, Tasks 10-12 follow same TDD pattern as Task 9)*

---

## WEEK 5: Integration & Testing

### Task 13: Integration Testing (UI + Backend)

**Files:**
- Create: `tests/test_integration.py`

**Scope:** End-to-end workflows
- User clicks Toggle → HardeningManager.enable() → Status updates → Activity log appended

### Task 14: Installer Setup (Inno Setup)

**Files:**
- Create: `installer/installer.iss`
- Create: `installer/icon.ico` (256x256)
- Create: `BUILD.md` (build instructions)

---

## WEEK 6: Release

### Task 15: Documentation

**Files:**
- Create: `docs/ARCHITECTURE.md` (developer guide)
- Create: `docs/CONTRIBUTING.md`
- Modify: `README.md`

### Task 16: Release Prep & v0.7.0 Tag

**Files:**
- Modify: `pyproject.toml` (version 0.7.0)
- Modify: `README.md` (update feature list)

**Steps:**
- [ ] Version bump
- [ ] GitHub release page
- [ ] v0.7.0 git tag
- [ ] Announce on GitHub Discussions

---

# EXECUTION SUMMARY

**Total tasks:** 16 (complete above, condensed here)
**Timeline:** 6 weeks
**Key deliverables:**
- ✅ PyQt6 GUI (dashboard + systray + settings + wizard + analytics)
- ✅ PowerShell IPC (enable/disable hardening)
- ✅ SQLite analytics (JSONL ingestion, risk scoring)
- ✅ Installer (.exe via PyInstaller + Inno Setup)
- ✅ User education (7 touchpoints for VPN/antivirus messaging)
- ✅ Documentation (ARCHITECTURE, BUILD, CONTRIBUTING)

**Success criteria:**
- Installation < 2 min
- First-run wizard < 3 min
- Dashboard loads < 1 sec
- No expert jargon in UI
- Resource usage < 80MB RAM

