"""Core business logic and system integration for OpenGuard.

This package contains backend logic for communicating with PowerShell scripts,
data processing, and system operations.
"""

from src.core.config_manager import ConfigManager
from src.core.hardening_manager import HardeningManager
from src.core.process_monitor import ProcessMonitor

__all__ = ["ConfigManager", "HardeningManager", "ProcessMonitor"]
