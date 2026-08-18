# OpenGuard v0.7.0 — Implementation Progress

**Plan:** docs/superpowers/plans/2026-08-04-openguard-v0.7-implementation.md  
**Start:** 2026-08-04  
**Status:** v0.7.0 core plan complete (16/16) + Task 17 post-release fix ✅

---

## Task Status

### Week 1: Foundation
- [x] Task 1: Project Setup & Dependencies ✅ (commits d61541b..322de98)
- [x] Task 2: Base Application Class ✅ (commit 3cb1989)
- [x] Task 3: Main Window — Status Card & Activity Log ✅ (commit 45d57d9)
- [x] Task 4: System Tray Integration ✅ (commits acacd15..c1ce000, review clean)

### Week 2-3: UI Components
- [x] Task 5: Settings Dialog (Tabs) ✅ (commits 871c1e2..47ab86c, review clean)
- [x] Task 6: Onboarding Wizard (4-Screen Flow) ✅ (commits f4c5edc..ee5f8d3, review clean)
- [x] Task 7: Analytics Modal ✅ (commits 76e69d7..7fa4f8f, review clean)
- [x] Task 8: UI Styles & Dark Mode ✅ (commit 6ae49c6, review clean)

### Week 4: Backend Integration
- [x] Task 9: HardeningManager (PowerShell IPC) ✅ (commit f555d68, review clean)
- [x] Task 10: AnalyticsEngine (JSONL → SQLite) ✅ (commit 98e2e67, review clean)
- [x] Task 11: ConfigManager (YAML I/O) ✅ (commit 8afc365, review clean)
- [x] Task 12: ProcessMonitor (Watch PowerShell) ✅ (commit bd6ca12, review clean)

### Week 5: Integration & Testing
- [x] Task 13: Integration Testing (UI + Backend) ✅ (commit 9c8a43b)
- [x] Task 14: Installer Setup (Inno Setup) ✅ (commit c794f43)

### Week 6: Release
- [x] Task 15: Documentation ✅ (commits 88703e5, ea88776)
- [x] Task 16: Release Prep & v0.7.0 Tag ✅ (commit d7d2b56, tag v0.7.0)

### Post-release fixes (found via live testing on real machine)
- [x] fix: stop claiming protection before any has been applied (commit e2b5cfa)
- [x] fix: give the PowerShell backend a callable entry point (commit 10de3f4)
- [x] fix: base protection status on evidence OpenGuard actually left behind (commit 8c91fdd)
- [x] Task 17: surface hardening risk advisory (VPN/antivirus disclaimer) in GUI ✅ (commits fb65ba8, fix d180ebc, review clean — safety/honesty-critical: GUI previously showed a bare green "Protection enabled" without OpenGuard.ps1's own disclaimer that it does not encrypt traffic or eliminate MITM risk)
- [x] feat: keep the activity log after the window closes (commit 691005b — applied outside the subagent-driven-development workflow, not independently reviewed)
- [x] Task 18: stop counting self-generated system events (protection toggle, advisory, errors) as detected threats ✅ (commit 3b7675e, review clean — safety/honesty-critical: found live when toggling protection 6 times during testing produced "Threats Blocked: 6, Risk: HIGH" with zero actual attacks, because AnalyticsModal/AnalyticsEngine counted any WARN/ERROR event regardless of category; ProcessMonitor from Task 12 is still not wired into src/app.py, so no real threat detector exists yet — risk stats now correctly read 0/LOW until one is)

- [x] Task 19: correct onboarding wizard completion screen ("Protection is now ON" was false — finishing the wizard only saves Settings, never calls enable_hardening()) ✅ (commit f66f6c0, review clean — project owner chose wording fix over auto-enabling hardening on wizard finish)

- [x] fix: rename Settings dialog "Analytics" tab to "Logging" ✅ (commit 717df77 — resolved naming collision with systray's separate "📊 Analytics" menu item)
- [x] Task 20: wire Settings.dark_mode into the actual rendered theme, including live re-theming of already-open windows on save ✅ (commit c0cb1e2, review clean — Dark Mode checkbox previously persisted to disk but had zero visual effect, every get_stylesheet() call site was hardcoded dark_mode=True)

- [x] Task 21: replace systray's plain circle icon with a shield silhouette (green+checkmark protected, red+X unprotected) ✅ (commit d61ee6b, review clean — approved with two non-blocking notes: the shield silhouette itself isn't independently pinned by a dedicated test beyond the mark-presence tests, and one reported test-count delta included in-flight unrelated changes)
- [x] Task 22: generate installer/icon.ico (green shield + Cinzel "OG" monogram + checkmark badge, 256x256 multi-res) ✅ (commit 2573dfd, review clean — the file Task 14's brief required but never got; font bundled at installer/assets/fonts/Cinzel-Bold.ttf, OFL-licensed)
- [x] fix: point installer.iss and BUILD.md at the real branding icon, retire the undesigned openguard.ico placeholder ✅ (commit 91e9cf8)
- [x] Task 23: theme SettingsDialog's QTabWidget tab page bodies (found live immediately after Task 20 — dialog frame correctly followed dark_mode, but tab page content stayed Qt's native gray regardless of theme; root cause was get_stylesheet() never targeting plain QWidget tab pages, same class of issue already fixed for QWizardPage) ✅ (commit f0aced7, review clean — QWidget#tabPage objectName-scoped selector, verified live by pixel-sampling both themes)
- [x] fix: retire the undesigned installer/openguard.ico placeholder, repoint installer.iss + BUILD.md at the real icon.ico ✅ (commit 91e9cf8 — Task 14's implementer named its placeholder openguard.ico instead of following its own brief's icon.ico filename; Task 22 correctly built icon.ico per spec but couldn't repoint installer.iss/BUILD.md, out of its scope)
- [x] housekeeping: moved 4 stray task report files (task-12, 13, 14, 16) from repo root into .superpowers/sdd/ (gitignored scratch dir), where they belonged — left uncommitted/untracked at root since some point in Week 4-6, never cleaned up

- [x] Task 24: wire ProcessMonitor into the running app, fix pipe leak (stdout/stderr now DEVNULL not PIPE) and category bug (its own start/stop/error bookkeeping now category="system", was "process_monitor" which would have miscounted as a real threat under Task 18's filter) ✅ (commit 26f1056, review clean, docstring follow-up 9413852 — explicitly does NOT add real threat-detection logic; it only reflects whether the monitoring subprocess itself is alive, confirmed with project owner as the deliberate scope)
- [x] Task 25: make Settings.systray_enabled take effect live on save (was only read once at setup_ui() time, same "declared but not live-wired" pattern Task 20 fixed for dark_mode, never applied here) ✅ (commit 9937ec6, review clean)
- [x] Task 26: give MainWindow its own Settings button, wired to the same _on_settings_requested handler the tray uses ✅ (commit d9423c4, review clean — closes a real usability trap Task 25 made newly reachable: before Task 25, systray_enabled had no live effect so Settings was always reachable via the tray regardless of the checkbox; after Task 25, a user could disable the tray and permanently lock themselves out of Settings with no other entry point anywhere in the app)

### Known gaps identified during guided live walkthrough (2026-08-17), not yet fixed
- `Settings.auto_start` persists to config.yaml and is shown in the UI but is never used anywhere to actually create/remove a Windows startup entry (Registry Run key or Startup folder shortcut) — the checkbox is currently cosmetic.
- The systray's "Help" menu item is a no-op (`_on_help_clicked` is `pass`).
- Onboarding wizard and Settings dialog remain English-only; main window disclaimer (Task 17) and activity log advisory text are Turkish. Project constraint states "Turkish UI, English code" but localization was explicitly deferred early in the project and remains incomplete.
- No code-signing certificate — installer triggers Windows SmartScreen "unknown publisher" warnings. Discussed with project owner; Azure Trusted Signing (~$120/year, individual-eligible) identified as the most fitting option, not yet purchased/applied.
- Not distributed via winget/Chocolatey/Microsoft Store — GitHub Releases is currently the only channel.
- No auto-update mechanism.
- Pro-tier UI exists as a stub (AnalyticsModal's "Upgrade" text) with no real payment/licensing backend — matches the original spec's explicit deferral of monetization to v0.8.0.

---

## Completed Tasks

All 16 planned tasks + Task 17 (post-release safety fix) complete and review-approved. v0.7.0 verified working end-to-end on a real Windows machine (admin-elevated hardening enable/disable cycle confirmed via registry check).

---

## Known Issues / Minor Findings

- Task 5: unused `import pytest` in tests/test_ui/test_settings_dialog.py after app fixture removal (trivial, non-blocking; flag for final whole-branch review cleanup pass)
- Commit 691005b ("keep the activity log after the window closes") was made outside the tracked subagent-driven-development review workflow — no review record exists for it. Worth a lightweight pass if a formal audit trail matters before shipping.
