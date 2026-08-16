"""Generate ``installer/icon.ico``: a green shield with an "OG" Cinzel-Bold
monogram and a circular checkmark status badge.

This is a build-time/asset-generation script, not application code -- it is
never imported by ``src/``. Run it standalone from the repository root:

    python installer/generate_icon.py

It requires Pillow, which is declared under the ``assets`` optional
dependency group rather than the app's runtime dependencies:

    pip install -e ".[assets]"

The design always uses the "protected" green/checkmark styling: this is a
static, install-time branding asset (Task 22), not a live status indicator
like the systray icon (Task 21) -- it never reflects an unprotected state.

Running this script is deterministic and idempotent: it always regenerates
``installer/icon.ico`` from scratch, so re-running it after design tweaks to
this file is always safe.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python installer/generate_icon.py` to be run directly (with the
# repository root NOT on sys.path, since only the script's own directory is
# added automatically) while still importing the app's color constants
# instead of hardcoding hex values.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from src.ui.styles import COLOR_SAFE, COLOR_TEXT_DARK  # noqa: E402

INSTALLER_DIR = Path(__file__).resolve().parent
FONT_PATH = INSTALLER_DIR / "assets" / "fonts" / "Cinzel-Bold.ttf"
OUTPUT_PATH = INSTALLER_DIR / "icon.ico"

CANVAS_SIZE = 256
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

# A fixed, hand-picked darker shade of COLOR_SAFE (#22C55E) for the status
# badge. This is a static branding asset -- an exact color-math derivation
# isn't required, just something that reads as "a shade darker than the
# shield" (see task-22 brief).
BADGE_GREEN = "#15803D"
CHECK_WHITE = "#FFFFFF"

ShieldBox = tuple[int, int, int, int]  # left, top, right, bottom
Point = tuple[float, float]


def _quad_bezier(p0: Point, control: Point, p1: Point, steps: int = 24) -> list[Point]:
    """Sample a quadratic Bezier curve from p0 to p1, inclusive of both ends."""
    points = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * control[0] + t**2 * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * control[1] + t**2 * p1[1]
        points.append((x, y))
    return points


def _draw_shield(draw: ImageDraw.ImageDraw, fill: str) -> ShieldBox:
    """Draw the shield silhouette and return its bounding box.

    The shield is a rounded-top rectangle (the shoulders) unioned with a
    curved lower half whose sides sweep smoothly inward to a point at the
    bottom -- both shapes are filled with the same color on the same
    canvas, so the overlap merges into a single shield silhouette.
    """
    left, right = 40, 216
    top = 24
    rect_bottom = 120
    cx = (left + right) // 2
    apex_y = 236

    draw.rounded_rectangle((left, top, right, rect_bottom), radius=28, fill=fill)

    taper = apex_y - rect_bottom
    right_curve = _quad_bezier(
        (right, rect_bottom - 1), (right, rect_bottom - 1 + taper * 0.7), (cx, apex_y)
    )
    left_curve = _quad_bezier(
        (cx, apex_y), (left, rect_bottom - 1 + taper * 0.7), (left, rect_bottom - 1)
    )
    outline = [(left, rect_bottom - 1)] + right_curve + left_curve[1:]
    draw.polygon(outline, fill=fill)

    return left, top, right, apex_y


def _draw_monogram(image: Image.Image, shield_box: ShieldBox) -> None:
    """Render "OG" in Cinzel Bold, centered in the shield's upper-middle."""
    left, top, right, bottom = shield_box
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(str(FONT_PATH), 76)
    font.set_variation_by_name("Bold")

    center_x = (left + right) // 2
    center_y = top + int((bottom - top) * 0.34)
    draw.text((center_x, center_y), "OG", font=font, fill=COLOR_TEXT_DARK, anchor="mm")


def _draw_badge(image: Image.Image, shield_box: ShieldBox) -> None:
    """Draw the circular status badge with a checkmark, lower-right of the shield."""
    left, top, right, bottom = shield_box
    shield_width = right - left

    # Roughly 1/3 of the shield's width, per the approved mockup proportions.
    diameter = shield_width // 3
    radius = diameter // 2
    # Nudged in from the right edge so the badge overlaps the shield's
    # lower-right corner without extending far past its outer silhouette.
    center = (right - radius - 6, bottom - int((bottom - top) * 0.27))

    draw = ImageDraw.Draw(image)
    bbox = (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius)
    draw.ellipse(bbox, fill=BADGE_GREEN)

    check_width = max(3, radius // 5)
    p1 = (center[0] - radius * 0.5, center[1] - radius * 0.02)
    p2 = (center[0] - radius * 0.12, center[1] + radius * 0.4)
    p3 = (center[0] + radius * 0.55, center[1] - radius * 0.35)
    draw.line([p1, p2, p3], fill=CHECK_WHITE, width=check_width, joint="curve")


def generate() -> Path:
    """Generate ``installer/icon.ico`` and return the path it was written to."""
    image = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    shield_box = _draw_shield(draw, COLOR_SAFE)
    _draw_monogram(image, shield_box)
    _draw_badge(image, shield_box)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_PATH, format="ICO", sizes=ICO_SIZES)
    return OUTPUT_PATH


if __name__ == "__main__":
    written_path = generate()
    print(f"Wrote {written_path}")
