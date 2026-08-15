"""Tests for the contract between HardeningManager and the PowerShell backend.

The Python side invoked `-Action Enable -Level Moderate` against a script that
declared no parameters at all and instead dropped into an interactive menu
loop, so the toggle could never have worked in any environment.

Get-Command parses the script and reports its parameter metadata without
executing it, so these tests never touch the firewall.
"""

import json
import subprocess

import pytest

from src.core.hardening_manager import HardeningManager


def _declared_parameters(script_path):
    """Return the parameter names the script declares, without running it."""
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"(Get-Command '{script_path}').Parameters.Keys | ConvertTo-Json",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        pytest.fail(f"could not parse {script_path}: {result.stderr.strip()}")

    return set(json.loads(result.stdout or "[]"))


@pytest.fixture(scope="module")
def declared():
    return _declared_parameters(HardeningManager()._resolve_backend_path())


class TestBackendAcceptsWhatWeSend:
    """Every argument the manager passes must exist on the script."""

    def test_script_declares_action(self, declared):
        """-Action selects enable, disable or status without the menu."""
        assert "Action" in declared

    def test_script_declares_level(self, declared):
        """-Level carries the configured firewall level through."""
        assert "Level" in declared

    def test_every_argument_the_manager_sends_is_declared(self, declared):
        """Guards against the two sides drifting apart again."""
        manager = HardeningManager()
        sent = {
            arg.lstrip("-")
            for arg in manager._build_command("Enable", "-Level", "Moderate")
            if arg.startswith("-")
        }
        powershell_own = {"NoProfile", "ExecutionPolicy", "File"}

        assert (sent - powershell_own) <= declared
