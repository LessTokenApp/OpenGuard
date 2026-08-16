"""Manages PowerShell hardening subprocess for OpenGuard.

This module handles inter-process communication (IPC) with the PowerShell backend
script (OpenGuard.ps1) to enable/disable system hardening features.
"""

import re
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

# Fallback advisory text when RISK UYARISI block cannot be parsed from stdout
FALLBACK_ADVISORY = (
    "Bu aracı, trafiği şifrelemez. Dinleme ve MITM riskini ortadan kaldırmaz. "
    "Sadece cihazın keşfedilmesini zorlaştırır."
)


class HardeningManager(QObject):
    """Manages PowerShell hardening subprocess.

    This class provides a Qt-based interface to communicate with the OpenGuard
    PowerShell backend script for enabling and disabling system hardening.

    Signals:
        status_changed: Emitted when hardening status changes (bool: is_protected)
        error_occurred: Emitted when an error occurs (str: error message)
        advisory_raised: Emitted after successful hardening with advisory text (str: advisory)
    """

    status_changed = pyqtSignal(bool)  # is_protected
    error_occurred = pyqtSignal(str)  # error message
    advisory_raised = pyqtSignal(str)  # advisory text

    def __init__(self):
        """Initialize HardeningManager.

        Sets up the backend path and initial protection status.
        """
        super().__init__()
        self.backend_path = self._resolve_backend_path()
        self.is_protected = False

    @staticmethod
    def _parse_risk_advisory(stdout: str) -> str:
        """Extract the RISK UYARISI advisory block from PowerShell stdout.

        Looks for the RISK UYARISI block delimited by ============ lines,
        extracts the advisory text between them, and removes blank lines.

        If the block is not found, returns the fallback advisory text.

        Args:
            stdout: The captured stdout from the PowerShell subprocess

        Returns:
            str: The advisory text (parsed or fallback)
        """
        if not stdout:
            return FALLBACK_ADVISORY

        # Pattern to match the RISK UYARISI block
        # Matches: equals line, RISK UYARISI header, advisory lines, equals line
        pattern = r"={10,}.*?RISK UYARISI.*?={10,}"
        match = re.search(pattern, stdout, re.DOTALL | re.IGNORECASE)

        if not match:
            return FALLBACK_ADVISORY

        # Extract the matched block
        block = match.group(0)

        # Split by lines and filter out the delimiters and header
        lines = block.split("\n")
        advisory_lines = []

        for line in lines:
            stripped = line.strip()
            # Skip empty lines, delimiter lines, and the RISK UYARISI header
            if stripped and not stripped.startswith("=") and "RISK UYARISI" not in stripped:
                advisory_lines.append(stripped)

        if not advisory_lines:
            return FALLBACK_ADVISORY

        # Join the advisory lines with newlines
        return "\n".join(advisory_lines)

    @staticmethod
    def _resolve_backend_path() -> Path:
        """Locate the PowerShell entry script for the current environment.

        PyInstaller does not bundle the .ps1 files, and the installer copies
        them to {app}\\scripts, so a frozen build looks beside the executable.
        A source checkout uses the script at the repository root.

        Returns:
            Path: Location of OpenGuard.ps1, which may not exist.
        """
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent / "scripts" / "OpenGuard.ps1"

        return Path(__file__).resolve().parents[2] / "OpenGuard.ps1"

    def _build_command(self, action: str, *extra: str) -> list[str]:
        """Assemble the argv for a backend call.

        argv is a list rather than a string so that an installed path such as
        C:\\Program Files\\OpenGuard\\scripts is passed as one argument instead
        of being split on its space. The shipped script is unsigned, so the
        execution policy is bypassed for this invocation only.

        Args:
            action: Value for the script's -Action parameter.
            *extra: Additional arguments appended after the action.

        Returns:
            list[str]: Full argument vector for subprocess.
        """
        return [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.backend_path),
            "-Action",
            action,
            *extra,
        ]

    def enable_hardening(self, level: str = "Moderate") -> bool:
        """Call PowerShell to enable hardening.

        Args:
            level: Hardening level (e.g., "Low", "Moderate", "High").
                   Defaults to "Moderate".

        Returns:
            bool: True if hardening was enabled successfully, False otherwise.
        """
        try:
            result = subprocess.run(
                self._build_command("Enable", "-Level", level),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.is_protected = True
                self.status_changed.emit(True)
                # Parse and emit the advisory text
                advisory_text = self._parse_risk_advisory(result.stdout)
                self.advisory_raised.emit(advisory_text)
                return True
            else:
                error_msg = result.stderr or "Hardening failed"
                self.error_occurred.emit(error_msg)
                return False
        except subprocess.TimeoutExpired as e:
            self.error_occurred.emit(f"Process timeout: {str(e)}")
            return False
        except Exception as e:
            self.error_occurred.emit(str(e))
            return False

    def disable_hardening(self) -> bool:
        """Disable hardening.

        Returns:
            bool: True if hardening was disabled successfully, False otherwise.
        """
        try:
            result = subprocess.run(
                self._build_command("Disable"),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.is_protected = False
                self.status_changed.emit(False)
                return True
            else:
                error_msg = result.stderr or "Disable failed"
                self.error_occurred.emit(error_msg)
                return False
        except subprocess.TimeoutExpired as e:
            self.error_occurred.emit(f"Process timeout: {str(e)}")
            return False
        except Exception as e:
            self.error_occurred.emit(str(e))
            return False

    def get_status(self) -> bool:
        """Ask the system whether hardening is currently applied.

        This used to return an in-memory flag that only this process ever set,
        so a machine that really was hardened still reported as unprotected.

        The backend answers through its exit code: 0 active, 1 inactive.
        Anything else means the question could not be answered, most often
        because privileges were missing. That resolves to False: a tool that
        reports whether someone is exposed must never turn "unknown" into
        "protected".

        Returns:
            bool: True only when the backend confirms hardening is applied.
        """
        try:
            result = subprocess.run(
                self._build_command("Status"),
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.is_protected = False
            return False

        if result.returncode == 0:
            self.is_protected = True
        else:
            if result.returncode != 1:
                self.error_occurred.emit(
                    result.stderr.strip() or f"Status check failed ({result.returncode})"
                )
            self.is_protected = False

        return self.is_protected
