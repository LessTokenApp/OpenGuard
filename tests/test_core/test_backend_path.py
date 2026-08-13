"""Tests for locating the PowerShell backend script.

The manager hardcoded a relative `.\\backend\\OpenGuard.ps1`, a directory that
exists in no environment: the repository keeps the script at its root and the
installer deploys it to {app}\\scripts. Every hardening call therefore failed.
"""

import sys

from src.core.hardening_manager import HardeningManager


class TestBackendScriptLocation:
    """The manager must resolve a script path that actually exists."""

    def test_resolved_path_exists_when_running_from_source(self):
        """Running from a source checkout must find the repository's script."""
        manager = HardeningManager()

        assert manager.backend_path.exists(), f"backend script not found at {manager.backend_path}"

    def test_resolved_path_points_at_the_powershell_entry_point(self):
        """The resolved file must be the OpenGuard entry script."""
        manager = HardeningManager()

        assert manager.backend_path.name == "OpenGuard.ps1"

    def test_frozen_build_looks_beside_the_executable(self, monkeypatch, tmp_path):
        """When frozen, the script ships next to the exe under scripts/.

        PyInstaller does not bundle the .ps1 files; the installer copies them to
        {app}\\scripts, so a frozen build must look there rather than inside the
        extracted bundle.
        """
        exe_dir = tmp_path / "app"
        scripts = exe_dir / "scripts"
        scripts.mkdir(parents=True)
        expected = scripts / "OpenGuard.ps1"
        expected.write_text("# stub")

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", str(exe_dir / "OpenGuard.exe"))

        manager = HardeningManager()

        assert manager.backend_path == expected
