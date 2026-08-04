"""Event dataclass for activity logging."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    """Represents an event for activity logging.

    Attributes:
        timestamp: When the event occurred
        event: Description of the event
        severity: Event severity level ("SUCCESS", "WARN", "ERROR")
        category: Optional category for the event (default: "")
    """

    timestamp: datetime
    event: str
    severity: str  # "SUCCESS", "WARN", "ERROR"
    category: str = ""

    def __post_init__(self) -> None:
        """Validate event data after initialization."""
        valid_severities = {"SUCCESS", "WARN", "ERROR"}
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity '{self.severity}'. Must be one of: "
                f"{', '.join(valid_severities)}"
            )
