# Verifying Your Download

Windows will warn you when you run the OpenGuard installer. This page explains
exactly why, and how to check the file yourself without having to take our word
for anything.

---

## Why Windows shows a warning

When you run `OpenGuard-Setup-0.7.0.exe`, Windows SmartScreen will show:

> **Windows protected your PC**
> Microsoft Defender SmartScreen prevented an unrecognised app from starting.

**This is accurate and you should not ignore it.** It means what it says:
Windows has no cryptographic proof of who published this file.

OpenGuard is not yet signed with a code signing certificate. Certificates cost
money every year and require a hardware security key; OpenGuard is currently
free and funded by donations, so that has not happened yet. Once it does, the
warning goes away on its own.

What the warning does **not** mean:

- It does not mean the file was scanned and found malicious.
- It does not mean Windows detected anything in the file at all.

SmartScreen is reporting an absence of evidence, not evidence of a problem. That
distinction matters, but it also means the warning gives you no assurance in
either direction. The checks below are how you get real assurance.

---

## How to check the file yourself

### 1. Compare the checksum

Every release publishes a SHA-256 hash. Compute the hash of your download and
compare it:

```powershell
Get-FileHash .\OpenGuard-Setup-0.7.0.exe -Algorithm SHA256
```

Compare the output against the hash shown on the
[release page](https://github.com/LessTokenApp/OpenGuard/releases). They must
match exactly, character for character.

**What this proves:** the file reached you intact and is byte-for-byte identical
to what was published. It rules out corruption in transit and tampering by
anything sitting between GitHub and your machine.

**What it does not prove:** that the published file is trustworthy. If the
release itself were compromised, the hash would match the compromised file. A
checksum verifies integrity, not intent. For that, use the checks below.

### 2. Scan it with multiple engines

Upload the installer to [VirusTotal](https://www.virustotal.com). It runs the
file against several dozen antivirus engines at once, which is considerably
more informative than any single scanner.

Read the results with the next section in mind.

### 3. Build it yourself

This is the strongest check available, and the reason OpenGuard is open source.
You do not have to trust any binary we produce:

```bash
git clone https://github.com/LessTokenApp/OpenGuard.git
cd OpenGuard
```

[BUILD.md](../BUILD.md) documents the full build. Every command there is
verified to run from a clean checkout.

Note that builds are **not** byte-for-byte reproducible: Inno Setup embeds a
timestamp, so your installer will have a different hash than the published one
even when the source is identical. You can compare the application files under
`dist/OpenGuard/` rather than the installer itself.

### 4. Read the source

OpenGuard is MIT licensed and the entire source is public. The parts worth
reading first, if you want to know what it does to your system:

| File | What it does |
|------|--------------|
| [`OpenGuard-Hardening.ps1`](../OpenGuard-Hardening.ps1) | Firewall rules and DNS changes |
| [`src/core/hardening_manager.py`](../src/core/hardening_manager.py) | Decides when those run |
| [`src/core/process_monitor.py`](../src/core/process_monitor.py) | Process monitoring |

---

## Why antivirus software may flag OpenGuard

Some scanners will report OpenGuard, and the reason is worth understanding
rather than dismissing.

OpenGuard's actual job requires it to:

- Add and remove Windows Firewall rules
- Change system DNS settings
- Launch PowerShell as a subprocess
- Enumerate running processes
- Request Administrator privileges

That list is a fair description of OpenGuard. It is also a fair description of
a lot of malware, and heuristic scanners cannot tell the difference from
behaviour alone. On top of that, the application is packaged with PyInstaller,
which bundles a Python interpreter — a technique legitimate software and
malware both use, and which several engines treat as suspicious by default.

So a detection here is usually a **false positive driven by behaviour and
packaging**, not by anything found in the code. But "usually" is not "always",
which is why the verification steps above exist. Do not take our word for it:
check the hash, scan it, or build it from source.

If a scanner flags a build, please
[open an issue](https://github.com/LessTokenApp/OpenGuard/issues) with the
engine name and detection label so it can be submitted for reclassification.

---

## Why OpenGuard asks for Administrator

Windows Firewall rules and system DNS settings are machine-wide, and Windows
does not allow an unelevated process to change either. There is no way to do
what OpenGuard does without elevation.

OpenGuard does not encrypt your traffic and is not a VPN. See
[Telemetry](../README.md#telemetry) in the README for what it does and does not
do.

---

## If you would rather wait

That is a completely reasonable choice. If an unsigned installer is not
something you want to run, wait for a signed release. Watch the
[releases page](https://github.com/LessTokenApp/OpenGuard/releases) — signing is
on the roadmap, and the release notes will say when a build is signed.
