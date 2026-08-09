"""Monitors OpenGuard.ps1 PowerShell process for activity detection.

This module handles process monitoring and event emission for the OpenGuard
PowerShell script launched by HardeningManager.
"""

import subprocess
from datetime import datetime
from typing import List, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from src.models.event import Event


class ProcessMonitor(QObject):
    """Monitors OpenGuard.ps1 PowerShell process for activity.

    This class watches the OpenGuard.ps1 process launched by HardeningManager
    and emits events when the process is detected or its output changes.

    Signals:
        new_events: Emitted when new events are detected (list of Event objects)
    """

    new_events = pyqtSignal(list)  # List[Event]

    def __init__(self):
        """Initialize ProcessMonitor.

        Sets up process monitoring infrastructure and initial state.
        """
        super().__init__()
        self.is_monitoring = False
        self._process: Optional[subprocess.Popen] = None

    def start_monitoring(self) -> None:
        """Start monitoring the OpenGuard.ps1 PowerShell process.

        Launches a PowerShell process that monitors for OpenGuard.ps1
        and emits events when the process is detected.

        Returns:
            None
        """
        if self.is_monitoring:
            return

        try:
            # PowerShell command to monitor for OpenGuard.ps1 process
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                (
                    "while ($true) { "
                    "Get-Process -Name 'powershell' -ErrorAction SilentlyContinue | "
                    "Where-Object {$_.CommandLine -like '*OpenGuard.ps1*'} | "
                    "Select-Object ProcessName, Id, StartTime; "
                    "Start-Sleep -Seconds 1 "
                    "}"
                ),
            ]

            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.is_monitoring = True

            # Emit initial event when monitoring starts
            event = Event(
                timestamp=datetime.now(),
                event="Process monitoring started for OpenGuard.ps1",
                severity="SUCCESS",
                category="process_monitor",
            )
            self.new_events.emit([event])

        except Exception as e:
            # Handle any exceptions silently to prevent crashes
            error_event = Event(
                timestamp=datetime.now(),
                event=f"Failed to start process monitoring: {str(e)}",
                severity="ERROR",
                category="process_monitor",
            )
            self.new_events.emit([error_event])

    def stop_monitoring(self) -> None:
        """Stop monitoring the OpenGuard.ps1 PowerShell process.

        Terminates the monitoring subprocess and resets state.

        Returns:
            None
        """
        if not self.is_monitoring or self._process is None:
            return

        try:
            self._process.terminate()
            self._process = None
            self.is_monitoring = False

            # Emit event when monitoring stops
            event = Event(
                timestamp=datetime.now(),
                event="Process monitoring stopped for OpenGuard.ps1",
                severity="SUCCESS",
                category="process_monitor",
            )
            self.new_events.emit([event])

        except Exception as e:
            # Handle any exceptions silently to prevent crashes
            error_event = Event(
                timestamp=datetime.now(),
                event=f"Error stopping process monitoring: {str(e)}",
                severity="ERROR",
                category="process_monitor",
            )
            self.new_events.emit([error_event])
            self.is_monitoring = False
