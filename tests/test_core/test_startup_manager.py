"""Tests for startup_manager, which registers/unregisters OpenGuard's Windows
startup entry under HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run.

winreg must never be touched for real during tests: every winreg call used by
the implementation is patched at src.core.startup_manager.winreg.<Function>,
matching the subprocess-patching style already used for
test_hardening_manager.py / test_process_monitor.py.
"""

import sys
from unittest.mock import MagicMock, patch

from src.core import startup_manager

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "OpenGuard"


class TestGetStartupCommand:
    """get_startup_command() must only ever point at a real frozen executable."""

    def test_returns_quoted_executable_path_when_frozen(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", r"C:\Program Files\OpenGuard\OpenGuard.exe")

        command = startup_manager.get_startup_command()

        assert command == r'"C:\Program Files\OpenGuard\OpenGuard.exe"'

    def test_returns_empty_string_when_not_frozen(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        assert startup_manager.get_startup_command() == ""

    def test_returns_empty_string_when_frozen_attribute_absent(self, monkeypatch):
        monkeypatch.delattr(sys, "frozen", raising=False)

        assert startup_manager.get_startup_command() == ""


class TestEnable:
    """enable() must create/update the registry Run value only when frozen."""

    @patch("src.core.startup_manager.winreg.CloseKey")
    @patch("src.core.startup_manager.winreg.SetValueEx")
    @patch("src.core.startup_manager.winreg.CreateKeyEx")
    def test_writes_registry_value_when_frozen(
        self, mock_create_key, mock_set_value, mock_close_key, monkeypatch
    ):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", r"C:\Apps\OpenGuard.exe")
        mock_handle = MagicMock()
        mock_create_key.return_value = mock_handle

        startup_manager.enable()

        mock_create_key.assert_called_once()
        args, kwargs = mock_create_key.call_args
        # HKEY_CURRENT_USER and the Run key path must be used.
        assert startup_manager.winreg.HKEY_CURRENT_USER in args
        assert RUN_KEY_PATH in args

        mock_set_value.assert_called_once()
        set_value_args = mock_set_value.call_args[0]
        assert set_value_args[0] is mock_handle
        assert set_value_args[1] == VALUE_NAME
        assert set_value_args[3] == startup_manager.winreg.REG_SZ
        assert set_value_args[4] == r'"C:\Apps\OpenGuard.exe"'

    @patch("src.core.startup_manager.winreg.SetValueEx")
    @patch("src.core.startup_manager.winreg.CreateKeyEx")
    def test_does_nothing_when_not_frozen(self, mock_create_key, mock_set_value, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)

        startup_manager.enable()

        mock_create_key.assert_not_called()
        mock_set_value.assert_not_called()


class TestDisable:
    """disable() must remove the value, and tolerate it already being absent."""

    @patch("src.core.startup_manager.winreg.CloseKey")
    @patch("src.core.startup_manager.winreg.DeleteValue")
    @patch("src.core.startup_manager.winreg.OpenKey")
    def test_deletes_the_value_when_present(
        self, mock_open_key, mock_delete_value, mock_close_key
    ):
        mock_handle = MagicMock()
        mock_open_key.return_value = mock_handle

        startup_manager.disable()

        mock_delete_value.assert_called_once_with(mock_handle, VALUE_NAME)

    @patch("src.core.startup_manager.winreg.CloseKey")
    @patch("src.core.startup_manager.winreg.DeleteValue")
    @patch("src.core.startup_manager.winreg.OpenKey")
    def test_does_not_raise_when_value_already_absent(
        self, mock_open_key, mock_delete_value, mock_close_key
    ):
        mock_open_key.return_value = MagicMock()
        mock_delete_value.side_effect = FileNotFoundError()

        startup_manager.disable()  # must not raise

    @patch("src.core.startup_manager.winreg.OpenKey")
    def test_does_not_raise_when_key_itself_is_absent(self, mock_open_key):
        mock_open_key.side_effect = FileNotFoundError()

        startup_manager.disable()  # must not raise


class TestIsEnabled:
    """is_enabled() must reflect the mocked registry read."""

    @patch("src.core.startup_manager.winreg.CloseKey")
    @patch("src.core.startup_manager.winreg.QueryValueEx")
    @patch("src.core.startup_manager.winreg.OpenKey")
    def test_true_when_value_present(self, mock_open_key, mock_query_value, mock_close_key):
        mock_open_key.return_value = MagicMock()
        mock_query_value.return_value = (r'"C:\Apps\OpenGuard.exe"', 1)

        assert startup_manager.is_enabled() is True

    @patch("src.core.startup_manager.winreg.OpenKey")
    def test_false_when_key_absent(self, mock_open_key):
        mock_open_key.side_effect = FileNotFoundError()

        assert startup_manager.is_enabled() is False

    @patch("src.core.startup_manager.winreg.CloseKey")
    @patch("src.core.startup_manager.winreg.QueryValueEx")
    @patch("src.core.startup_manager.winreg.OpenKey")
    def test_false_when_value_absent(self, mock_open_key, mock_query_value, mock_close_key):
        mock_open_key.return_value = MagicMock()
        mock_query_value.side_effect = FileNotFoundError()

        assert startup_manager.is_enabled() is False


class TestApply:
    """apply() must delegate to enable()/disable() based on the flag."""

    @patch("src.core.startup_manager.disable")
    @patch("src.core.startup_manager.enable")
    def test_apply_true_calls_enable(self, mock_enable, mock_disable):
        startup_manager.apply(True)

        mock_enable.assert_called_once()
        mock_disable.assert_not_called()

    @patch("src.core.startup_manager.disable")
    @patch("src.core.startup_manager.enable")
    def test_apply_false_calls_disable(self, mock_enable, mock_disable):
        startup_manager.apply(False)

        mock_disable.assert_called_once()
        mock_enable.assert_not_called()
