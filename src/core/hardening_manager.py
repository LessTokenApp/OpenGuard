"""Manages PowerShell hardening subprocess for OpenGuard.

This module handles inter-process communication (IPC) with the PowerShell backend
script (OpenGuard.ps1) to enable/disable system hardening features.
"""

import subprocess
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal


class HardeningManager(QObject):
    """Manages PowerShell hardening subprocess.

    This class provides a Qt-based interface to communicate with the OpenGuard
    PowerShell backend script for enabling and disabling system hardening.

    Signals:
        status_changed: Emitted when hardening status changes (bool: is_protected)
        error_occurred: Emitted when an error occurs (str: error message)
    """

    status_changed = pyqtSignal(bool)  # is_protected
    error_occurred = pyqtSignal(str)   # error message

    def __init__(self):
        """Initialize HardeningManager.

        Sets up the backend path and initial protection status.
        """
        super().__init__()
        self.backend_path = (
            Path(__file__).parent.parent.parent / "backend" / "OpenGuard.ps1"
        )
        self.is_protected = False

    def enable_hardening(self, level: str = "Moderate") -> bool:
        """Call PowerShell to enable hardening.

        Args:
            level: Hardening level (e.g., "Low", "Moderate", "High").
                   Defaults to "Moderate".

        Returns:
            bool: True if hardening was enabled successfully, False otherwise.
        """
        try:
            cmd = (
                f'powershell.exe -NoProfile -Command '
                f'"& {{.\\backend\\OpenGuard.ps1 -Action Enable -Level {level}}}"'
            )
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                self.is_protected = True
                self.status_changed.emit(True)
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
            cmd = (
                f'powershell.exe -NoProfile -Command '
                f'"& {{.\\backend\\OpenGuard.ps1 -Action Disable}}"'
            )
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
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
        """Get current protection status.

        Returns:
            bool: True if system is protected, False otherwise.
        """
        return self.is_protected
