"""Tests for how the PowerShell backend is invoked.

subprocess is intercepted rather than executed: these calls change firewall
rules and DNS settings, which a test must never do to the machine running it.
"""

import subprocess

import pytest

from src.core.hardening_manager import HardeningManager


@pytest.fixture
def captured_command(monkeypatch):
    """Capture the argv handed to subprocess.run without running anything."""
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return captured


class TestBackendInvocation:
    """The backend must be launched in a way that survives real install paths."""

    def test_enable_invokes_the_resolved_script(self, captured_command):
        """The command must reference the resolved path, not a guessed one."""
        manager = HardeningManager()

        manager.enable_hardening()

        assert str(manager.backend_path) in captured_command["cmd"]

    def test_script_path_is_a_single_argument(self, captured_command):
        """A path under Program Files contains a space.

        Passing argv as a list keeps that path intact; string concatenation
        would split it and the installed build would never launch.
        """
        manager = HardeningManager()

        manager.enable_hardening()

        cmd = captured_command["cmd"]
        assert isinstance(cmd, list), "argv must be a list so paths are not split"
        assert str(manager.backend_path) in cmd

    def test_enable_passes_the_requested_level(self, captured_command):
        """The chosen firewall level must reach the script."""
        manager = HardeningManager()

        manager.enable_hardening(level="Basic")

        assert "Basic" in captured_command["cmd"]

    def test_disable_requests_the_disable_action(self, captured_command):
        """Disabling must ask the script for the Disable action."""
        manager = HardeningManager()

        manager.disable_hardening()

        assert "Disable" in captured_command["cmd"]

    def test_execution_policy_is_bypassed(self, captured_command):
        """The shipped script is unsigned, so the default policy would block it."""
        manager = HardeningManager()

        manager.enable_hardening()

        assert "Bypass" in captured_command["cmd"]
