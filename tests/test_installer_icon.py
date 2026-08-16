"""Tests for the generated installer icon and its source assets.

Task 14's brief required `installer/icon.ico` but it was never created.
These tests guard the generated asset's existence and basic validity, not
the drawing internals of `installer/generate_icon.py` -- pixel-level
assertions would be brittle for a design asset that may get tweaked.
"""

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = REPO_ROOT / "installer" / "icon.ico"
FONT_PATH = REPO_ROOT / "installer" / "assets" / "fonts" / "Cinzel-Bold.ttf"
FONT_LICENSE_PATH = REPO_ROOT / "installer" / "assets" / "fonts" / "OFL.txt"


class TestInstallerIcon:
    """installer/icon.ico must exist and be a valid multi-resolution ICO."""

    def test_icon_file_exists(self):
        assert ICON_PATH.is_file()

    def test_icon_is_a_valid_ico(self):
        with Image.open(ICON_PATH) as image:
            image.verify()

    def test_icon_contains_256_and_16_frames(self):
        with Image.open(ICON_PATH) as image:
            assert image.format == "ICO"
            sizes = image.ico.sizes()
            assert (256, 256) in sizes
            assert (16, 16) in sizes


class TestBundledFontAssets:
    """The Cinzel font and its license must stay bundled -- the icon script
    depends on both, and OFL.txt is required for license compliance."""

    def test_cinzel_font_exists(self):
        assert FONT_PATH.is_file()

    def test_font_license_exists(self):
        assert FONT_LICENSE_PATH.is_file()
