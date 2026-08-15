"""Every shipped PowerShell script must be readable by Windows PowerShell 5.1.

HardeningManager invokes powershell.exe, which is Windows PowerShell 5.1, not
pwsh. 5.1 reads a file without a byte order mark using the system ANSI code
page, so a UTF-8 file carrying non-ASCII characters is decoded wrongly and the
parser reports a misleading syntax error somewhere unrelated. OpenGuard.ps1
failed this way and could not run at all, while parsing cleanly under
PowerShell 7 where the default is UTF-8.

These tests parse each script rather than executing it, so no firewall rule,
DNS setting or registry value is touched.
"""

import subprocess

import pytest

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
SCRIPTS = sorted(REPO_ROOT.rglob("*.ps1"))
SCRIPTS = [p for p in SCRIPTS if "venv" not in p.parts and "dist" not in p.parts]


def _parse_errors(script):
    """Return parse errors reported by Windows PowerShell 5.1, if any."""
    command = (
        "$e=$null; "
        f"[void][System.Management.Automation.Language.Parser]::ParseFile('{script}',"
        "[ref]$null,[ref]$e); "
        'if($e){ $e | ForEach-Object { "line $($_.Extent.StartLineNumber): $($_.Message)" } }'
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        timeout=90,
    )
    return result.stdout.strip()


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_script_parses_under_windows_powershell(script):
    """A script that will not parse cannot run, whatever it is passed."""
    errors = _parse_errors(script)

    assert not errors, f"{script.name} does not parse under 5.1:\n{errors}"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_non_ascii_scripts_carry_a_byte_order_mark(script):
    """Without a BOM, 5.1 decodes non-ASCII with the wrong code page."""
    raw = script.read_bytes()
    if not any(byte > 127 for byte in raw):
        pytest.skip("pure ASCII, decoding is unambiguous")

    assert raw.startswith(
        b"\xef\xbb\xbf"
    ), f"{script.name} holds non-ASCII characters but has no UTF-8 BOM"
