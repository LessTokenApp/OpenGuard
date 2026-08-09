# OpenGuard Architecture Guide

## Overview

OpenGuard is a professional Python GUI application for Windows 11+ system hardening. It features a multi-layered architecture with clear separation between UI, business logic, and system integration layers.

**Version:** 0.7.0  
**Python:** 3.12+  
**Framework:** PyQt6 6.6.0+

---

## Architecture Layers

### 1. **Presentation Layer (UI)**
Located in: `src/ui/`

The presentation layer handles all user interface components and user interactions using PyQt6.

#### Components:
- **`main_window.py`**: Main application window
  - Displays protection status card
  - Provides toggle protection button
  - Shows activity log with recent events
  - Emits signals for user actions

- **`styles.py`**: Stylesheet management
  - Provides centralized styling for PyQt6 components
  - Supports dark mode and light mode themes
  - Uses CSS variables for consistent theming

- **`settings_dialog.py`**: Settings management UI
  - Allows users to configure hardening levels
  - Manages firewall settings
  - Handles user preferences

- **`analytics_modal.py`**: Analytics display
  - Shows threat timeline visualization
  - Displays event analytics with risk scoring
  - Implements FREE/PRO tier UI restrictions

- **`onboarding_wizard.py`**: Initial setup wizard
  - 4-screen onboarding flow for new users
  - Introduction → Features → Configuration → Ready

#### Signal Flow:
- User interactions (clicks, inputs) emit PyQt signals
- Signals are connected to business logic handlers
- Status updates propagate back through signals to refresh UI

---

### 2. **Application Layer**
Located in: `src/`

The application layer orchestrates the lifecycle and initialization.

#### Components:
- **`app.py`**: OpenGuardApp class
  - Inherits from QApplication
  - Manages application metadata and styling
  - Controls main window initialization
  - Manages event loop execution

- **`main.py`**: Entry point
  - Creates OpenGuardApp instance
  - Starts the application

---

### 3. **Business Logic Layer (Core)**
Located in: `src/core/`

The core layer implements business logic and system operations.

#### Components:
- **`hardening_manager.py`**: PowerShell integration
  - Manages IPC with PowerShell backend (OpenGuard.ps1)
  - Enables/disables system hardening
  - Supports multiple hardening levels: Low, Moderate, High
  - Emits signals: `status_changed(bool)`, `error_occurred(str)`

- **`analytics_engine.py`**: Event analytics
  - Reads event data from JSONL files
  - Stores events in SQLite database (~/.openguard/events.db)
  - Calculates risk scores
  - Generates threat timelines
  - Supports event filtering and aggregation

- **`config_manager.py`**: Configuration management
  - Loads/saves YAML configuration (~/.openguard/config.yaml)
  - Handles Settings serialization
  - Provides sensible defaults
  - Cross-platform path handling using pathlib

- **`process_monitor.py`**: Process monitoring
  - Monitors system processes
  - Detects suspicious activity
  - Generates alerts
  - Integrates with analytics engine

---

### 4. **Data Layer (Models)**
Located in: `src/models/`

The data layer defines data structures.

#### Components:
- **`event.py`**: Event dataclass
  - Represents system events
  - Fields: timestamp, event, severity, category
  - Severity levels: SUCCESS, WARN, ERROR
  - Validation in `__post_init__`

- **`settings.py`**: Settings dataclass
  - User configuration and preferences
  - Firewall levels: Basic, Moderate, Relaxed
  - Stores user choices and state

---

## Signal Flow Architecture

### User Action → UI Update Flow

```
┌─────────────────────────────────────────────────────────┐
│                   User Interaction                        │
│              (Click Button, Change Setting)               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   UI Signal Emission          │
        │  (toggle_protection_clicked)  │
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │   Business Logic Handler      │
        │   (HardeningManager, etc.)    │
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │  System Operation             │
        │  (PS1 Subprocess Call)        │
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │  Status Signal Emission       │
        │  (status_changed, error_*)    │
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │   UI State Update             │
        │   (MainWindow.update_status)  │
        └──────────────────────────────┘
```

### Event Processing Flow

```
┌─────────────────────┐
│   PowerShell Event  │ (OpenGuard.ps1 generates)
│   (JSONL file)      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────┐
│ AnalyticsEngine.read_jsonl()│
│ Parse JSONL events          │
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ Store in SQLite             │
│ (~/.openguard/events.db)    │
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ Calculate Risk Scores       │
│ Generate Threat Timeline    │
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ Analytics Modal             │
│ Display to User             │
└─────────────────────────────┘
```

---

## Inter-Process Communication (IPC) with PowerShell

### Overview
OpenGuard's Python GUI communicates with the PowerShell backend (`OpenGuard.ps1`) using subprocess IPC. This allows the Python application to execute system-level operations with administrative privileges.

### IPC Architecture

```
┌────────────────────────────────────┐
│  Python GUI Layer                  │
│  (PyQt6 - Qt Event Loop)           │
└─────────┬────────────────────────┐
          │                        │
          ▼                        ▼
  ┌──────────────┐      ┌────────────────┐
  │ Enable Call  │      │  Disable Call  │
  └──────┬───────┘      └────────┬───────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │ HardeningManager       │
         │ subprocess.run() call  │
         └─────────┬──────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌────────┐ ┌──────┐ ┌─────────┐
    │ stdout │ │stderr│ │ retcode │
    └────────┘ └──────┘ └─────────┘
        │          │          │
        └──────────┼──────────┘
                   │
                   ▼
         ┌────────────────────────┐
         │ PowerShell Backend     │
         │ (OpenGuard.ps1)        │
         └─────────┬──────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   ┌──────────┐          ┌──────────┐
   │  Enable  │          │ Disable  │
   │ Hardening│          │ Hardening│
   └──────────┘          └──────────┘
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
         ┌────────────────────────┐
         │ System Registry/       │
         │ Firewall Changes       │
         └────────────────────────┘
```

### HardeningManager Implementation

**File:** `src/core/hardening_manager.py`

#### Command Execution:
```python
cmd = (
    f'powershell.exe -NoProfile -Command '
    f'"& {{.\\backend\\OpenGuard.ps1 -Action Enable -Level {level}}}"'
)
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
```

#### Parameters:
- `-Action`: Enable or Disable
- `-Level`: Hardening level (Low, Moderate, High)
- `-NoProfile`: Skip PowerShell profile loading for speed
- `timeout=30`: 30-second timeout for subprocess

#### Return Handling:
- **returncode 0**: Operation succeeded
- **returncode != 0**: Operation failed, error in stderr
- **TimeoutExpired**: Process took >30 seconds
- **Exception**: Other process errors

#### Signal Emission:
- `status_changed(bool)`: Emitted when status changes
- `error_occurred(str)`: Emitted when errors occur

### PowerShell Backend Integration Points

The PowerShell script (`OpenGuard.ps1`) handles:
1. Registry modifications for hardening
2. Windows Firewall configuration
3. DNS security settings (DoH detection)
4. Network monitoring setup
5. Event logging

Communication happens through:
- **Exit Codes**: 0 for success, non-zero for errors
- **stdout**: Non-error messages and status
- **stderr**: Error messages
- **Side Effects**: Registry/Firewall changes

---

## Data Storage

### Configuration
**Path:** `~/.openguard/config.yaml` (home directory)

```yaml
firewall_level: Moderate
dark_mode: true
last_action: Enable
timestamp: "2026-08-09T10:30:00"
```

### Event Database
**Path:** `~/.openguard/events.db` (SQLite)

**Schema:**
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event TEXT NOT NULL,
    severity TEXT NOT NULL,
    category TEXT DEFAULT ''
)
```

### Event Log (Legacy)
**Path:** `security_log.jsonl` (project directory)

**Format:** JSONL (one JSON event per line)
```json
{"timestamp": "2026-08-09T10:30:00", "event": "Hardening enabled", "severity": "SUCCESS"}
```

---

## Testing Architecture

### Test Structure
- Location: `tests/`
- Markers: unit, integration, ui
- Coverage: `tests/` directory
- Framework: pytest + pytest-cov + pytest-qt

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src

# Specific marker
pytest -m unit
```

---

## Directory Structure

```
OpenGuard/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point
│   ├── app.py                     # Application class
│   ├── core/
│   │   ├── __init__.py
│   │   ├── hardening_manager.py   # PS1 IPC
│   │   ├── analytics_engine.py    # Event processing
│   │   ├── config_manager.py      # Config I/O
│   │   └── process_monitor.py     # Process monitoring
│   ├── models/
│   │   ├── __init__.py
│   │   ├── event.py               # Event dataclass
│   │   └── settings.py            # Settings dataclass
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py         # Main UI
│       ├── settings_dialog.py     # Settings UI
│       ├── analytics_modal.py     # Analytics UI
│       ├── onboarding_wizard.py   # Onboarding UI
│       └── styles.py              # Theming
├── backend/
│   └── OpenGuard.ps1              # PowerShell backend
├── tests/
│   └── test_*.py
├── docs/
│   ├── ARCHITECTURE.md            # This file
│   ├── CONTRIBUTING.md            # Dev guide
│   └── ...
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Dependencies

### Core
- **PyQt6** (6.6.0+): GUI framework
- **PyYAML** (6.0+): Configuration serialization

### Development
- **pytest** (7.4.0+): Testing framework
- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking
- **isort**: Import sorting

---

## Performance Considerations

1. **IPC Latency**: PowerShell subprocess calls (~100-200ms)
2. **Database Queries**: SQLite for local event storage
3. **UI Responsiveness**: Signals/slots for non-blocking operations
4. **Memory**: Event database can grow; implement retention policy
5. **Startup Time**: PowerShell profile skip (-NoProfile) for speed

---

## Security Considerations

1. **Admin Privileges**: PowerShell backend requires admin rights
2. **Input Validation**: All user inputs validated before PS1 calls
3. **Error Handling**: Sensitive errors logged, generic errors shown to user
4. **IPC Security**: Subprocess execution from trusted paths only
5. **Data Storage**: Config and events stored in user home directory
6. **No Credentials**: Never store passwords or sensitive credentials

---

## Future Extensibility

The architecture supports:
- Plugin system for additional hardening rules
- Custom event processors
- Multiple backend implementations
- Distributed event aggregation
- Webhook integrations for alerts
