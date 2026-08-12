# Release Notes Template

Paste this into the GitHub release body and fill in the blanks. The checksum
block is not optional: [VERIFYING.md](VERIFYING.md) tells users that every
release publishes a hash, and that promise only holds if this is done each time.

Upload both the installer and its `.sha256` sidecar file as release assets.

---

## OpenGuard vX.Y.Z

_One or two sentences on what changed and who should care._

### Changes

- ...

### Download

**[OpenGuard-Setup-X.Y.Z.exe](link)** — Windows 11 (build 22000) or later, Administrator required

### Verifying this download

This build is **not code signed**, so Windows SmartScreen will warn you that
the publisher is unrecognised. Check the file yourself instead of clicking
through the warning:

```powershell
Get-FileHash .\OpenGuard-Setup-X.Y.Z.exe -Algorithm SHA256
```

Expected SHA-256:

```
PASTE_HASH_HERE
```

Full instructions, including how to build from source instead:
[docs/VERIFYING.md](https://github.com/LessTokenApp/OpenGuard/blob/master/docs/VERIFYING.md)

### Known limitations

- Not code signed; SmartScreen will warn on first run
- Antivirus engines may flag the build — see VERIFYING.md for why
- Does not encrypt traffic; not a VPN replacement

---

## Pre-release checklist

- [ ] Version bumped in `pyproject.toml`, `installer/installer.iss`, and `README.md`
- [ ] `pytest` passes
- [ ] Clean build from a wiped `dist/` and `build/`, following BUILD.md
- [ ] Installer runs on a clean machine: installs, launches, uninstalls
- [ ] `.sha256` sidecar generated from the exact uploaded file, **from inside
      the output directory** so it records a bare filename and validates where
      the user downloads it:
      ```bash
      cd dist/installer
      sha256sum OpenGuard-Setup-X.Y.Z.exe > OpenGuard-Setup-X.Y.Z.exe.sha256
      sha256sum -c OpenGuard-Setup-X.Y.Z.exe.sha256   # must print OK
      ```
- [ ] Hash in the release body matches the uploaded asset
- [ ] If the build is signed, say so explicitly — users are watching for it
