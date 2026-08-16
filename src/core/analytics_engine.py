"""Analytics engine for reading, processing, and analyzing event data."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from src.models.event import Event


class AnalyticsEngine:
    """Engine for managing event analytics with JSONL input and SQLite storage.

    This engine handles reading event data from JSONL files, storing them in SQLite,
    and providing analytics such as risk scores and threat timelines.
    """

    def __init__(self, db_path: str | Path = None) -> None:
        """Initialize the AnalyticsEngine.

        Args:
            db_path: Path to the SQLite database file. If None, uses default app data directory.
        """
        if db_path is None:
            # Use default app data directory
            app_data = Path.home() / ".openguard"
            app_data.mkdir(parents=True, exist_ok=True)
            db_path = app_data / "events.db"
        else:
            db_path = Path(db_path)

        self.db_path = db_path
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize the database
        self._init_database()

        self.log_file = self.db_path.parent / "events.jsonl"
        self.events: List[Event] = (
            self.read_jsonl(self.log_file) if Path(self.log_file).exists() else []
        )

    def _init_database(self) -> None:
        """Initialize the SQLite database and create tables if needed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event TEXT NOT NULL,
                severity TEXT NOT NULL,
                category TEXT DEFAULT ''
            )
            """)

        conn.commit()
        conn.close()

    def read_jsonl(self, path: str) -> List[Event]:
        """Read events from a JSONL file.

        Args:
            path: Path to the JSONL file

        Returns:
            List of Event objects parsed from the JSONL file

        Raises:
            FileNotFoundError: If the JSONL file does not exist
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {path}")

        events = []
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    event = Event(
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        event=data.get("event", ""),
                        severity=data.get("severity", "SUCCESS"),
                        category=data.get("category", ""),
                    )
                    events.append(event)
                except (json.JSONDecodeError, KeyError, ValueError):
                    # Skip malformed lines
                    continue

        return events

    def record(self, event: Event) -> None:
        """Add an event to the store and write it out.

        Args:
            event: The event to keep.
        """
        self.events.append(event)
        self.save_events()

    def save_events(self) -> None:
        """Write the current events to the JSONL log.

        The file is rewritten rather than appended to, so saving twice cannot
        duplicate an entry.
        """
        path = Path(self.log_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            for event in self.events:
                f.write(
                    json.dumps(
                        {
                            "timestamp": event.timestamp.isoformat(),
                            "event": event.event,
                            "severity": event.severity,
                            "category": event.category,
                        }
                    )
                    + "\n"
                )

    def ingest_to_sqlite(self, events: List[Event]) -> int:
        """Ingest events into the SQLite database.

        Args:
            events: List of Event objects to insert

        Returns:
            Number of events inserted into the database
        """
        if not events:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for event in events:
            cursor.execute(
                """
                INSERT INTO events (timestamp, event, severity, category)
                VALUES (?, ?, ?, ?)
                """,
                (
                    event.timestamp.isoformat(),
                    event.event,
                    event.severity,
                    event.category,
                ),
            )

        conn.commit()
        conn.close()

        return len(events)

    def get_24h_risk_score(self) -> str:
        """Calculate risk score based on WARN/ERROR events in the last 24 hours.

        System/administrative events (category="system") are excluded from risk scoring.
        Only genuine threat detections from external or internal monitors count.

        Risk score calculation:
        - 0 events: "LOW"
        - 1-2 events: "MEDIUM"
        - 3+ events: "HIGH"

        Returns:
            str: Risk score as "LOW", "MEDIUM", or "HIGH"
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate the timestamp from 24 hours ago
        now = datetime.now()
        cutoff_time = (now - timedelta(hours=24)).isoformat()

        # Count WARN and ERROR events in the last 24 hours, excluding system/administrative events
        cursor.execute(
            """
            SELECT COUNT(*) FROM events
            WHERE timestamp >= ?
            AND severity IN ('WARN', 'ERROR')
            AND category != 'system'
            """,
            (cutoff_time,),
        )

        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            return "LOW"
        elif count <= 2:
            return "MEDIUM"
        else:
            return "HIGH"

    def get_threat_timeline(self, days: int = 7) -> List[Event]:
        """Retrieve threat events from the last N days, sorted by timestamp.

        System/administrative events (category="system") are excluded from the threat timeline.
        Only genuine threat detections from external or internal monitors are included.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            List of Event objects sorted by timestamp (oldest first)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate the timestamp from N days ago
        now = datetime.now()
        cutoff_time = (now - timedelta(days=days)).isoformat()

        # Retrieve threat events from the last N days, excluding system/administrative events
        cursor.execute(
            """
            SELECT timestamp, event, severity, category FROM events
            WHERE timestamp >= ?
            AND category != 'system'
            ORDER BY timestamp ASC
            """,
            (cutoff_time,),
        )

        events = []
        for row in cursor.fetchall():
            event = Event(
                timestamp=datetime.fromisoformat(row[0]),
                event=row[1],
                severity=row[2],
                category=row[3],
            )
            events.append(event)

        conn.close()

        return events
