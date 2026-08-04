# OpenGuard v0.7.0 — GUI Redesign & Python Rewrite Specification

**Date:** August 4, 2026  
**Version:** 1.0  
**Status:** Approved for Implementation  
**Author:** AI-assisted design with user approval  

---

## Executive Summary

OpenGuard v0.7.0 transforms from a PowerShell CLI tool into a **professional, user-friendly Windows GUI application** targeting non-technical users on public WiFi. The redesign prioritizes:

1. **Installation simplicity** — One-click .exe installer, no PowerShell intimidation
2. **Trust-building UI** — Dashboard with real-time threat blocking feedback
3. **Accessibility** — Clear language, visual status indicators, tooltips
4. **Monetization foundation** — Free core + Pro tier for advanced features

**Target User:** Students, freelancers, remote workers, travelers using public WiFi (Starbucks, airports, hotels) who want to protect against MITM attacks, DNS spoofing, and data theft.

---

## Strategic Decision: Python GUI (PyQt6)

### Alternatives Considered

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **A: Systray-only** | Lightweight, minimal | Hidden from users, low trust | ❌ Rejected |
| **B: Dashboard + Systray (Python)** | Modern, accessible, scalable | Moderate resource use | ✅ **SELECTED** |
| **C: Electron/React** | Cutting-edge design | Heavy, overkill for v0.7 | ⏳ v1.0+ only |

### Rationale

**B is optimal because:**
- Users see **instant visual feedback** (🟢 Protected) → builds trust
- **One-click installer** removes PowerShell intimidation
- **Scalable architecture** supports cross-platform (Linux/macOS v0.9+)
- **Professional appearance** drives viral adoption
- **Resource-efficient** (PyQt6 ≈ 60-80MB, vs Electron ≈ 150MB+)

---

## Architecture

### Tech Stack

```
Frontend:     PyQt6 (GUI framework)
Backend:      Python 3.12+ (core logic, IPC)
Engine:       PowerShell 5.1+ (battle-tested security logic)
Data:         SQLite (logs, analytics)
Config:       YAML (user settings)
Packaging:    PyInstaller → .exe
Installer:    Inno Setup (.iss)
```

### Project Structure

```
OpenGuard-GUI/
├── src/
│   ├── main.py                      # Entry point, app initialization
│   ├── ui/
│   │   ├── main_window.py           # Dashboard widget
│   │   ├── systray.py               # System tray integration
│   │   ├── settings_dialog.py       # Settings window
│   │   ├── onboarding_wizard.py     # First-run setup
│   │   ├── analytics_modal.py       # Analytics viewer
│   │   └── styles.py                # Color scheme, fonts, CSS
│   ├── core/
│   │   ├── hardening_manager.py     # PowerShell subprocess IPC
│   │   ├── analytics_engine.py      # Log parsing, risk scoring
│   │   ├── config_manager.py        # YAML config ↔ UI sync
│   │   └── process_monitor.py       # Watch .ps1 execution
│   └── models/
│       ├── threat.py                # Dataclass: Threat
│       ├── event.py                 # Dataclass: Event
│       └── settings.py              # Dataclass: Settings
├── backend/
│   └── OpenGuard.ps1                # (existing v0.6.0, refactored)
├── installer/
│   ├── installer.iss                # Inno Setup script
│   ├── icon.ico                     # App icon
│   └── banner.bmp                   # Installer banner
├── tests/
│   ├── test_ui.py                   # UI unit tests
│   ├── test_core.py                 # Core logic tests
│   └── test_integration.py          # End-to-end tests
├── docs/
│   ├── ARCHITECTURE.md              # Developer guide
│   ├── BUILD.md                     # Build instructions
│   └── CONTRIBUTING.md              # Contribution guidelines
├── pyproject.toml                   # Python project metadata
└── README.md
```

### Layered Architecture

```
┌─────────────────────────────────────────┐
│  PRESENTATION LAYER (PyQt6)             │
│  ├─ Main Window (Dashboard)             │
│  ├─ Systray Integration                 │
│  ├─ Settings Dialog                     │
│  ├─ Analytics Modal                     │
│  └─ Onboarding Wizard                   │
└──────────────┬──────────────────────────┘
               │ (async signals/slots)
┌──────────────▼──────────────────────────┐
│  APPLICATION LAYER (Python Core)        │
│  ├─ HardeningManager                    │
│  ├─ AnalyticsEngine                     │
│  ├─ ConfigManager                       │
│  └─ ProcessMonitor                      │
└──────────────┬──────────────────────────┘
               │ (subprocess IPC)
┌──────────────▼──────────────────────────┐
│  SECURITY ENGINE (PowerShell)           │
│  ├─ Enable-Hardening                    │
│  ├─ Enable-AdaptiveRules                │
│  ├─ Test-DNSSecurity                    │
│  └─ Invoke-NetworkWatch                 │
└──────────────┬──────────────────────────┘
               │ (JSONL logs)
┌──────────────▼──────────────────────────┐
│  DATA LAYER (SQLite + YAML)             │
│  ├─ events table                        │
│  ├─ threats table                       │
│  └─ config.yaml                         │
└─────────────────────────────────────────┘
```

---

## UI Components

### 1. Main Window (Dashboard)

**Purpose:** Central hub showing protection status, quick actions, recent activity.

**Layout:**
```
┌─────────────────────────────────────────────────┐
│ 🛡️ OpenGuard v0.7.0              [_] [−] [×]   │
├─────────────────────────────────────────────────┤
│                                                 │
│ ╔═════════════════════════════════════════════╗ │
│ ║ STATUS CARD                                 ║ │
│ ║ 🟢 PROTECTED                                ║ │
│ ║ Hardening: ON | Firewall: Moderate | DNS: ✓║ │
│ ║                                             ║ │
│ ║        [  TOGGLE PROTECTION  ]              ║ │
│ ╚═════════════════════════════════════════════╝ │
│                                                 │
│ RISK ASSESSMENT (24h)                          │
│ ├─ Status: LOW RISK                            │
│ ├─ Threats: 0                                  │
│ └─ Session: 2h 14m                             │
│                                                 │
│ RECENT ACTIVITY (scrollable)                   │
│ ├─ 15:30 🟢 Hardening activated               │
│ ├─ 15:32 🟡 DNS spoofing blocked              │
│ ├─ 15:45 🟢 Firewall: Moderate mode           │
│ └─ 16:00 🟢 Status check passed                │
│                                                 │
│ [⚙️ Settings] [? Help] [📊 Analytics]          │
│                                                 │
│ Minimize to tray: [×] closes to taskbar only  │
└─────────────────────────────────────────────────┘
```

**Key elements:**
- Status card is the visual anchor (large, prominent, colored)
- One-click toggle is the primary action
- Activity log builds user confidence ("something is happening")
- Always-on-top option for travelers

**Design notes:**
- Color scheme: Green (#22C55E) for safe, Red (#EF4444) for threat
- Font: Segoe UI (system default, no external dependencies)
- Dark mode by default (kahve dükkanı environs, eye strain)
- Responsive to window resize (not fixed-width)

---

### 2. System Tray Integration

**Right-click menu:**
```
🛡️ OpenGuard
├─ 🟢 Protected (status indicator)
├─ ─────────────
├─ 🔴 Disable (5 min)
├─ ⚙️  Settings
├─ 📊 Analytics
├─ ? Help
├─ ─────────────
└─ ✖️  Exit
```

**Single-click:** Restores main window (if minimized)

**Tooltip:** "OpenGuard: Protected | Last activity: 5 min ago"

**Icon states:**
- 🟢 Green = Protected
- 🟡 Yellow = Warning
- 🔴 Red = Threat detected
- ⚫ Gray = Disabled

---

### 3. First-Run Onboarding Wizard

**4-screen progressive disclosure:**

1. **Welcome** — Relatable use case, clear value prop
2. **What it protects** — Specific threats (DNS spoof, MITM, gateway anomalies)
3. **Protection level** — Basic (recommended) / Moderate / Relaxed
4. **Ready!** — Show settings, tips, launch dashboard

**Design philosophy:**
- One question per screen (not overwhelming)
- Clear language (no jargon)
- Expand FAQ for curious users
- Always have [Back] and [Next/Finish] buttons

---

### 4. Settings Dialog

**Tabs:**

| Tab | Settings |
|-----|----------|
| 🛡️ **Protection** | Firewall level, DNS provider, network monitoring |
| 📊 **Analytics** | Auto-logging, retention, export |
| 🎨 **Appearance** | Dark mode, auto-start, systray behavior |
| 🔔 **Notifications** | Alert frequency, email (PRO) |

**Example: Protection tab**
```
Firewall Level:
○ Basic (DNS + Web only) — recommended
● Moderate (+ Email, SSH, NTP)
○ Relaxed (max compatibility)

DNS Security:
☑ Enable DoH
Provider: [Cloudflare ▼]

Network Monitoring:
☑ Monitor gateway MAC
☑ Alert on anomalies
```

---

### 5. Analytics Modal

**PRO-only advanced view:**
```
┌────────────────────────────────────┐
│ Analytics Dashboard            [×] │
├────────────────────────────────────┤
│                                    │
│ 📊 STATISTICS (Last 7 days)        │
│ • Total Events: 47                 │
│ • Threats Blocked: 3               │
│ • Session Time: 58h 14m            │
│                                    │
│ 📈 THREAT TIMELINE (graph)         │
│ [Line chart: 7-day trend]          │
│                                    │
│ 🔝 TOP THREATS                     │
│ 1. DNS Spoofing (2 blocks)        │
│ 2. Gateway Anomaly (1 block)      │
│ 3. Suspicious Query (0 blocks)    │
│                                    │
│ 📍 NETWORKS PROTECTED              │
│ • Starbucks (12 sessions)         │
│ • Airport (8 sessions)            │
│                                    │
│ [Export PDF] [Email Weekly]        │
│                                    │
└────────────────────────────────────┘
```

---

## Data Flow & IPC

### Communication Pattern

```
User clicks [Toggle Protection]
    ↓
PyQt6 MainWindow.on_toggle_clicked()
    ↓
HardeningManager.enable_hardening()
    ↓
Subprocess: powershell.exe -Command ".\OpenGuard.ps1 -Action Enable"
    ↓
PowerShell executes, logs to security_log.jsonl
    ↓
Python polls JSONL, parses new entries
    ↓
SQLite: INSERT into events table
    ↓
AnalyticsEngine: recalculate risk score
    ↓
PyQt6: Update UI (status, activity log, risk badge)
```

### Log Format (JSONL)

**Path:** `%APPDATA%\OpenGuard\security_log.jsonl`

```json
{"Timestamp": "2026-08-04 15:30:45", "Event": "Hardening acildi", "Severity": "SUCCESS"}
{"Timestamp": "2026-08-04 15:31:12", "Event": "Firewall rule: Moderate", "Severity": "SUCCESS"}
{"Timestamp": "2026-08-04 15:32:03", "Event": "DNS spoofing uyarisi", "Severity": "WARN"}
```

### SQLite Schema

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    event TEXT NOT NULL,
    severity TEXT NOT NULL,  -- SUCCESS, WARN, ERROR
    category TEXT,           -- HARDENING, DNS, FIREWALL, NETWORK
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE threats (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL,      -- DNS_SPOOF, GATEWAY_ANOMALY, etc
    timestamp DATETIME NOT NULL,
    blocked BOOLEAN,
    details TEXT
);

CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_threats_type ON threats(type);
```

### Risk Scoring Algorithm

```python
def calculate_risk_score(last_24h_events) -> str:
    threat_count = sum(1 for e in last_24h_events 
                       if e.severity in ["ERROR", "WARN"])
    
    if threat_count == 0:
        return "LOW"      # 🟢
    elif threat_count <= 2:
        return "MEDIUM"   # 🟡
    else:
        return "HIGH"     # 🔴
```

---

## Onboarding Flow

### Installation (User Perspective)

1. Download `OpenGuard-Setup-0.7.0.exe` from GitHub
2. Double-click → Installer runs (Inno Setup)
3. Accept license → Choose install location
4. Admin prompt (clear: "OpenGuard needs admin to protect your network")
5. Installation completes → First-run wizard launches automatically

### First-Run Wizard (4 screens)

**Screen 1: Welcome**
- Relatable headline: "Stay Safe on Public WiFi"
- Subtext: "Using Starbucks WiFi? Airport network?"
- Expandable FAQ
- [Next] button

**Screen 2: What it protects**
- ✅ DNS Spoofing
- ✅ MITM Attacks
- ✅ Network Sniffing
- ✅ Gateway Anomalies
- Note: "Does NOT encrypt traffic. Use with VPN."
- [Next] button

**Screen 3: Choose protection level**
- ⭐ **BASIC (recommended)** — Most users, minimal overhead
- MODERATE — Power users, more restrictive
- RELAXED — Legacy apps, compatibility mode
- [Next] button

**Screen 4: Ready!**
- Recap settings
- Pro tips (minimize to tray, check activity)
- [Finish] → dashboard opens

### Dashboard (Post-wizard)

- 🎉 Success notification: "Setup complete! You're protected now."
- Status: 🟢 PROTECTED
- Tip: "Minimize to tray. You'll stay protected."
- [Got it!] dismisses notification

---

## Monetization Strategy

### Freemium Model

**FREE tier:**
- ✅ Core protection (Hardening, Firewall, DNS, Monitoring)
- ✅ Basic analytics (last 24h summary)
- ✅ Settings, auto-start, systray
- ✅ Auto-updates
- ✅ Email support (48h response)

**PRO tier (₺259/year):**
- ✅ All FREE features
- ✅ Advanced analytics (7-day graphs, threat timeline)
- ✅ Email alerts (immediate + weekly digest)
- ✅ VPN status monitoring
- ✅ Scheduled hardening (auto-enable on WiFi)
- ✅ Priority support (4h response)
- ✅ Ad-free

### Upgrade Prompts

**Prompt #1:** Analytics screen (FREE users)
```
Want advanced insights?
• 7-day threat timeline
• Email alerts
• VPN integration
• Priority support

Just ₺259/year | [Upgrade Now]
```

**Prompt #2:** Email alerts feature
```
[PRO feature - Upgrade to enable]
[Unlock Now]
```

**Prompt #3:** After 30 days (subtle)
```
Loving OpenGuard? Consider PRO for advanced features.
[Learn more] [Dismiss]
```

### Trust & Transparency

**License screen:**
```
Current: FREE

Philosophy:
✓ No ads
✓ No data collection
✓ No telemetry
✓ Open-source (GitHub)

[Privacy Policy] [Source Code]
```

---

## Version Roadmap

| Version | Focus | Key Features |
|---------|-------|--------------|
| **v0.7.0** | GUI foundation | Python rewrite, dashboard, installer, onboarding |
| **v0.8.0** | UX polish | Design system, email alerts, VPN monitor, priority support |
| **v0.9.0** | Cross-platform | Linux, macOS versions |
| **v1.0.0** | Mature release | Installer refinement, auto-update, family tier |

---

## Success Criteria

### User-facing
1. ✅ Installation time < 2 minutes
2. ✅ First-run wizard < 3 minutes
3. ✅ Dashboard loads in < 1 second
4. ✅ Users understand "I'm protected" within 10 seconds
5. ✅ Zero expert jargon in UI

### Technical
1. ✅ Resource usage: < 80MB RAM, < 2% CPU idle
2. ✅ PowerShell subprocess calls async (no UI freeze)
3. ✅ Log polling every 5 seconds (responsive)
4. ✅ UI updates debounced (no flicker)
5. ✅ Test coverage: > 80%

### Business
1. ✅ Free users: easy upgrade prompts (not aggressive)
2. ✅ No ads, no data collection (trust building)
3. ✅ PRO tier differentiation clear (advanced analytics, alerts, support)

---

## Appendix: Design Tokens

### Colors (Light/Dark modes)

| Element | Light | Dark |
|---------|-------|------|
| Safe/Success | #22C55E | #86EFAC |
| Warning | #EAB308 | #FACC15 |
| Threat/Error | #EF4444 | #FCA5A5 |
| Background | #FFFFFF | #1F2937 |
| Text (primary) | #1F2937 | #F3F4F6 |
| Text (secondary) | #6B7280 | #D1D5DB |
| Border | #E5E7EB | #374151 |

### Typography

- **Font family:** Segoe UI (Windows default)
- **Body:** 11pt (system scaling aware)
- **Heading:** 14pt, semi-bold
- **Button:** 10pt, medium weight
- **Status card:** 16pt, bold

### Spacing

- **Margin unit:** 8px
- **Padding unit:** 8px
- **Card margin:** 16px
- **Button height:** 36px

---

## Timeline Estimate

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Week 1** | Setup, project skeleton | PyQt6 template, installer structure |
| **Week 2-3** | UI components | Dashboard, settings, wizard (no backend) |
| **Week 4** | Backend integration | HardeningManager, AnalyticsEngine |
| **Week 5** | Testing & Polish | Unit tests, UI polish, edge cases |
| **Week 6** | Release prep | Build .exe, documentation, GitHub release |

**Target launch:** v0.7.0 beta in 6 weeks

---

## Notes for Developers

- **No external dependencies beyond PyQt6, SQLite** (keep installer small)
- **PowerShell v0.6.0 core stays untouched** (reduce risk)
- **UI-first development** (mockups before code)
- **Keyboard-friendly** (tab navigation, Enter for actions)
- **Windows 11 focus, Windows 10 minimum** (modern UI, legacy compatibility)

---

**Design approved by user on 2026-08-04**  
**Status:** Ready for implementation planning
