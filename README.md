# OpenGuard Hardening

Professional Python GUI application for Windows 11+ system hardening and network security.

**English:** Professional system hardening tool with analytics and firewall management  
**Türkçe:** VPN'siz halka açık ağ sertleştirmesi - Windows 11+ için

---

## Features (v0.7.0)

### Core Hardening
- ✅ **Toggle Protection** - Enable/disable hardening with one click
- ✅ **Multi-Level Firewall** - 3 adaptive levels (Basic/Moderate/Relaxed)
- ✅ **DNS Security** - DoH detection and DNS over HTTPS management
- ✅ **Network Monitoring** - Real-time network activity monitoring

### User Experience
- ✅ **Modern GUI** - Professional PyQt6 interface with dark mode
- ✅ **Settings Management** - Persistent YAML-based configuration
- ✅ **Onboarding Wizard** - 4-screen guided setup for new users
- ✅ **System Tray Integration** - Easy access from desktop

### Analytics & Monitoring
- ✅ **Analytics Dashboard** - Threat timeline visualization
- ✅ **Risk Scoring** - Automated threat assessment
- ✅ **Event Logging** - JSONL format with SQLite storage
- ✅ **Free/Pro Tiers** - Feature-gated analytics dashboard

### Developer Features
- ✅ **PowerShell IPC** - Subprocess communication for system operations
- ✅ **Analytics Engine** - Event processing and storage
- ✅ **Config Manager** - YAML configuration I/O
- ✅ **Process Monitor** - System process tracking (TDD approach)
- ✅ **Qt Stylesheet System** - Centralized theming with dark mode

---

## Installation

### Option 1: Batch File (Recommended for Users)

```batch
1. Right-click "OpenGuard-Baslat.bat"
2. Select "Run as administrator"
3. Choose from menu
```

**Note:** Requires administrator privileges

### Option 2: Python Installation (For Developers)

#### Prerequisites
- Windows 11 Pro/Enterprise
- Python 3.12+ ([python.org](https://www.python.org))
- Administrator privileges

#### Steps

```bash
# Clone repository
git clone https://github.com/openguard/openguard.git
cd OpenGuard

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .

# Run application
python -m src.main
```

### Option 3: From Source

```bash
# Install with dev dependencies
pip install -e ".[dev,test]"

# Run quality checks
pytest && black src/ && ruff check src/

# Run application
python -m src.main
```

---

## Screenshots

### Main Window
![Main Window Screenshot Placeholder](docs/images/main-window-placeholder.png)
*Status card with protection toggle, activity log*

### Analytics Dashboard
![Analytics Dashboard Placeholder](docs/images/analytics-dashboard-placeholder.png)
*Threat timeline, risk scoring, event analytics*

### Settings Dialog
![Settings Dialog Placeholder](docs/images/settings-placeholder.png)
*Firewall levels, DNS settings, preferences*

### Onboarding Wizard
![Onboarding Wizard Placeholder](docs/images/onboarding-placeholder.png)
*4-screen setup flow for new users*

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Windows 11 Pro | Windows 11 Enterprise |
| **PowerShell** | 5.1+ | 7.0+ |
| **Python** | 3.12+ | 3.13+ |
| **Privileges** | Administrator | Admin + UAC off (testing) |
| **RAM** | 256 MB | 512 MB+ |

---

## Menu Options

### Main Menu
1. **Status Check** - Verify hardening status
2. **Enable Hardening** - Turn on protection
3. **Disable Hardening** - Turn off protection
4. **Aggressive Mode** - Enable with High level
5. **Adaptive Firewall** - Configure firewall rules
6. **DNS Security** - Manage DoH settings
7. **Network Monitoring** - Enable alerts
8. **User Guide** - View help documentation
9. **Settings** - Configure preferences
10. **Analytics Dashboard** - View threat timeline
11. **Exit** - Close application

---

## How It Works

### Architecture

OpenGuard uses a **4-layer architecture**:

1. **Presentation Layer** - PyQt6 GUI components
2. **Application Layer** - Event loop and lifecycle
3. **Business Logic** - Hardening, analytics, configuration
4. **System Integration** - PowerShell subprocess IPC

### Signal Flow

```
User Click → UI Signal → Business Logic → PowerShell → System Changes → Status Update → UI Refresh
```

For detailed architecture information, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Development

### Quick Start

```bash
# Clone and setup
git clone https://github.com/openguard/openguard.git
cd OpenGuard
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ".[dev,test]"

# Run tests
pytest -v

# Code quality
black src/ && ruff check --fix src/ && mypy src/

# Run app
python -m src.main
```

### Contributing

We welcome contributions! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- Development setup guide
- Testing instructions
- Git branch workflow
- Code quality standards
- Pull request process

### Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Layers, signal flow, IPC design
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Dev setup, testing, workflow
- **[README.md](README.md)** - This file (user guide)

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **GUI Framework** | PyQt6 | 6.6.0+ |
| **Language** | Python | 3.12+ |
| **Config** | YAML | 6.0+ |
| **Database** | SQLite | Built-in |
| **Backend** | PowerShell | 5.1+ |
| **Testing** | pytest | 7.4.0+ |

---

## Telemetry

OpenGuard **does not encrypt** internet traffic. It reduces the attack surface by:
- Blocking unauthorized inbound connections
- Securing DNS queries (DoH)
- Monitoring process activity
- Detecting anomalous network behavior

Your data stays on your system - no cloud uploads by default.

---

## License

MIT License - See [LICENSE](LICENSE) file for details

---

## Contact & Support

| Channel | Link |
|---------|------|
| **GitHub** | [github.com/NuraydinArikan/OpenGuard](https://github.com/NuraydinArikan/OpenGuard) |
| **Email** | info@lesstoken.app |
| **Issues** | [GitHub Issues](https://github.com/NuraydinArikan/OpenGuard/issues) |
| **Discussions** | [GitHub Discussions](https://github.com/NuraydinArikan/OpenGuard/discussions) |

---

## Changelog

| Version | Date | Highlights |
|---------|------|-----------|
| **v0.7.0** | Aug 2026 | Onboarding wizard, dark mode, process monitoring, enhanced analytics |
| **v0.6.0** | Aug 2026 | Analytics Dashboard integration |
| **v0.5.0** | Aug 2026 | PowerShell backend, firewall rules |

---

## Acknowledgments

Built with ❤️ using PyQt6, Python, and PowerShell.

**Maintainer:** Nuraydin Arikan

---

Last Updated: August 9, 2026 | OpenGuard v0.7.0
