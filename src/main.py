"""OpenGuard application entry point."""

import sys

from src.app import OpenGuardApp


def main() -> int:
    """Application entry point.

    Creates and runs the OpenGuard application.

    Returns:
        int: Exit code from the application
    """
    app = OpenGuardApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
