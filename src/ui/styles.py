"""Qt stylesheet system with dark mode support for OpenGuard UI."""

# Color tokens for status indicators
COLOR_SAFE = "#22C55E"      # Green
COLOR_WARN = "#EAB308"      # Amber
COLOR_ERROR = "#EF4444"     # Red

# Background and text colors
COLOR_BG_DARK = "#1F2937"   # Dark gray
COLOR_BG_LIGHT = "#FFFFFF"  # White
COLOR_TEXT_DARK = "#F3F4F6" # Light text
COLOR_TEXT_LIGHT = "#1F2937" # Dark text


def get_stylesheet(dark_mode: bool = True) -> str:
    """Return Qt stylesheet based on theme.

    Args:
        dark_mode: If True, returns dark theme stylesheet.
                  If False, returns light theme stylesheet.

    Returns:
        str: Qt stylesheet string for the theme
    """
    if dark_mode:
        bg = COLOR_BG_DARK
        text = COLOR_TEXT_DARK
        border = "#374151"
    else:
        bg = COLOR_BG_LIGHT
        text = COLOR_TEXT_LIGHT
        border = "#E5E7EB"

    return f"""
        QMainWindow, QDialog {{
            background-color: {bg};
            color: {text};
        }}

        QPushButton {{
            background-color: #3B82F6;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: #2563EB;
        }}

        QLabel {{
            color: {text};
        }}

        QTextEdit, QPlainTextEdit {{
            background-color: {bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
        }}

        QGroupBox {{
            color: {text};
            border: 1px solid {border};
            border-radius: 4px;
            margin-top: 6px;
            padding-top: 6px;
        }}
    """
