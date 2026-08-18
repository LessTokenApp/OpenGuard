"""Registers/unregisters OpenGuard's Windows startup entry.

Uses the standard library winreg module to manage a value under
HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run, matching
this project's existing Windows-only assumption (HardeningManager already
shells out to powershell.exe/OpenGuard.ps1 without any cross-platform guard).

Holds no state, so this is a small set of module-level functions rather than
a class, matching the style used elsewhere in src/core/ where a class isn't
needed to hold state (compare AnalyticsEngine/ConfigManager, which are
classes because they hold a db path / config path).
"""

import sys
import winreg

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "OpenGuard"


def get_startup_command() -> str:
    """Return the command that should be registered for auto-start.

    When running as a frozen PyInstaller executable (sys.frozen is True),
    this is the quoted path to the running .exe. Outside a frozen build
    (source/dev environment) there's no single correct executable to
    register, so an empty string is returned and callers should treat that
    as "not supported in this environment" rather than writing something
    wrong to the registry.
    """
    if not getattr(sys, "frozen", False):
        return ""

    return f'"{sys.executable}"'


def is_enabled() -> bool:
    """Return whether the OpenGuard startup entry currently exists."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH)
    except FileNotFoundError:
        return False

    try:
        winreg.QueryValueEx(key, VALUE_NAME)
        return True
    except FileNotFoundError:
        return False
    finally:
        winreg.CloseKey(key)


def enable() -> None:
    """Create/update the startup registry entry.

    No-op (does not raise, does not write anything) if get_startup_command()
    returns empty - i.e. running unfrozen. Callers can call enable()
    unconditionally from app code that doesn't know whether it's running
    frozen or from source.
    """
    command = get_startup_command()
    if not command:
        return

    key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH)
    try:
        winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)
    finally:
        winreg.CloseKey(key)


def disable() -> None:
    """Remove the startup registry entry if present.

    No-op if absent - does not raise FileNotFoundError or similar when
    there's nothing to remove.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE
        )
    except FileNotFoundError:
        return

    try:
        winreg.DeleteValue(key, VALUE_NAME)
    except FileNotFoundError:
        pass
    finally:
        winreg.CloseKey(key)


def apply(enabled: bool) -> None:
    """Convenience: enable() if enabled else disable()."""
    if enabled:
        enable()
    else:
        disable()
