"""Tests for AnalyticsEngine core module."""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.analytics_engine import AnalyticsEngine
from src.models.event import Event


class TestAnalyticsEngineInstantiation:
    """Test AnalyticsEngine creation and initialization."""

    def test_analytics_engine_creation(self, tmp_path):
        """Test AnalyticsEngine can be instantiated.

        Args:
            tmp_path: pytest temp directory fixture
        """
        engine = AnalyticsEngine(db_path=tmp_path / "test.db")
        assert engine is not None

    def test_analytics_engine_creates_database_directory(self, tmp_path):
        """Test AnalyticsEngine creates database directory if it doesn't exist.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "subdir" / "test.db"
        engine = AnalyticsEngine(db_path=db_path)
        assert db_path.parent.exists()

    def test_analytics_engine_creates_database_file(self, tmp_path):
        """Test AnalyticsEngine creates database file.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)
        # After initialization, the database file should exist
        assert db_path.exists()

    def test_analytics_engine_creates_events_table(self, tmp_path):
        """Test AnalyticsEngine creates events table in database.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)
        # Verify the events table exists by connecting to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
        )
        assert cursor.fetchone() is not None
        conn.close()


class TestReadJsonl:
    """Test read_jsonl functionality."""

    def test_read_jsonl_empty_file(self, tmp_path):
        """Test read_jsonl with an empty file.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)
        jsonl_path = tmp_path / "empty.jsonl"
        jsonl_path.touch()

        events = engine.read_jsonl(str(jsonl_path))
        assert events == []

    def test_read_jsonl_single_event(self, tmp_path):
        """Test read_jsonl with a single event.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)
        jsonl_path = tmp_path / "single.jsonl"

        # Create a single event in JSONL format
        now = datetime.now().isoformat()
        with open(jsonl_path, "w") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": now,
                        "event": "Test event",
                        "severity": "SUCCESS",
                        "category": "test",
                    }
                )
            )

        events = engine.read_jsonl(str(jsonl_path))
        assert len(events) == 1
        assert events[0].event == "Test event"
        assert events[0].severity == "SUCCESS"
        assert events[0].category == "test"

    def test_read_jsonl_multiple_events(self, tmp_path):
        """Test read_jsonl with multiple events.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)
        jsonl_path = tmp_path / "multiple.jsonl"

        # Create multiple events in JSONL format
        now = datetime.now()
        with open(jsonl_path, "w") as f:
            for i in range(3):
                event_time = (now - timedelta(hours=i)).isoformat()
                f.write(
                    json.dumps(
                        {
                            "timestamp": event_time,
                            "event": f"Test event {i}",
                            "severity": "SUCCESS",
                            "category": "test",
                        }
                    )
                    + "\n"
                )

        events = engine.read_jsonl(str(jsonl_path))
        assert len(events) == 3
        assert events[0].event == "Test event 0"
        assert events[1].event == "Test event 1"
        assert events[2].event == "Test event 2"

    def test_read_jsonl_with_different_severities(self, tmp_path):
        """Test read_jsonl with different severity levels.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)
        jsonl_path = tmp_path / "severities.jsonl"

        now = datetime.now().isoformat()
        with open(jsonl_path, "w") as f:
            for severity in ["SUCCESS", "WARN", "ERROR"]:
                f.write(
                    json.dumps(
                        {
                            "timestamp": now,
                            "event": f"Event with {severity}",
                            "severity": severity,
                        }
                    )
                    + "\n"
                )

        events = engine.read_jsonl(str(jsonl_path))
        assert len(events) == 3
        assert events[0].severity == "SUCCESS"
        assert events[1].severity == "WARN"
        assert events[2].severity == "ERROR"

    def test_read_jsonl_file_not_found(self, tmp_path):
        """Test read_jsonl with non-existent file.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        with pytest.raises(FileNotFoundError):
            engine.read_jsonl(str(tmp_path / "nonexistent.jsonl"))


class TestIngestToSqlite:
    """Test ingest_to_sqlite functionality."""

    def test_ingest_to_sqlite_empty_list(self, tmp_path):
        """Test ingest_to_sqlite with empty event list.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        count = engine.ingest_to_sqlite([])
        assert count == 0

    def test_ingest_to_sqlite_single_event(self, tmp_path):
        """Test ingest_to_sqlite with a single event.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        event = Event(
            timestamp=now, event="Test event", severity="SUCCESS", category="test"
        )

        count = engine.ingest_to_sqlite([event])
        assert count == 1

        # Verify the event was inserted
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        result = cursor.fetchone()
        assert result[0] == 1
        conn.close()

    def test_ingest_to_sqlite_multiple_events(self, tmp_path):
        """Test ingest_to_sqlite with multiple events.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(timestamp=now, event=f"Event {i}", severity="SUCCESS")
            for i in range(5)
        ]

        count = engine.ingest_to_sqlite(events)
        assert count == 5

        # Verify all events were inserted
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        result = cursor.fetchone()
        assert result[0] == 5
        conn.close()

    def test_ingest_to_sqlite_preserves_event_data(self, tmp_path):
        """Test ingest_to_sqlite preserves all event data.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        event = Event(
            timestamp=now,
            event="Important event",
            severity="ERROR",
            category="security",
        )

        engine.ingest_to_sqlite([event])

        # Verify the data was preserved
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT event, severity, category FROM events WHERE rowid = 1")
        result = cursor.fetchone()
        assert result[0] == "Important event"
        assert result[1] == "ERROR"
        assert result[2] == "security"
        conn.close()


class TestGet24hRiskScore:
    """Test get_24h_risk_score functionality."""

    def test_get_24h_risk_score_no_events(self, tmp_path):
        """Test get_24h_risk_score with no events in database.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        score = engine.get_24h_risk_score()
        assert score == "LOW"

    def test_get_24h_risk_score_only_success_events(self, tmp_path):
        """Test get_24h_risk_score with only SUCCESS events.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(timestamp=now, event=f"Event {i}", severity="SUCCESS")
            for i in range(5)
        ]
        engine.ingest_to_sqlite(events)

        score = engine.get_24h_risk_score()
        assert score == "LOW"

    def test_get_24h_risk_score_single_warn_event(self, tmp_path):
        """Test get_24h_risk_score with a single WARN event.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [Event(timestamp=now, event="Warning event", severity="WARN")]
        engine.ingest_to_sqlite(events)

        score = engine.get_24h_risk_score()
        assert score == "MEDIUM"

    def test_get_24h_risk_score_single_error_event(self, tmp_path):
        """Test get_24h_risk_score with a single ERROR event.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [Event(timestamp=now, event="Error event", severity="ERROR")]
        engine.ingest_to_sqlite(events)

        score = engine.get_24h_risk_score()
        assert score == "MEDIUM"

    def test_get_24h_risk_score_two_warn_events(self, tmp_path):
        """Test get_24h_risk_score with two WARN events.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(timestamp=now, event="Warning 1", severity="WARN"),
            Event(timestamp=now, event="Warning 2", severity="WARN"),
        ]
        engine.ingest_to_sqlite(events)

        score = engine.get_24h_risk_score()
        assert score == "MEDIUM"

    def test_get_24h_risk_score_three_error_events(self, tmp_path):
        """Test get_24h_risk_score with three ERROR events.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(timestamp=now, event="Error 1", severity="ERROR"),
            Event(timestamp=now, event="Error 2", severity="ERROR"),
            Event(timestamp=now, event="Error 3", severity="ERROR"),
        ]
        engine.ingest_to_sqlite(events)

        score = engine.get_24h_risk_score()
        assert score == "HIGH"

    def test_get_24h_risk_score_mixed_severity(self, tmp_path):
        """Test get_24h_risk_score with mixed severity events.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(timestamp=now, event="Success 1", severity="SUCCESS"),
            Event(timestamp=now, event="Warning 1", severity="WARN"),
            Event(timestamp=now, event="Error 1", severity="ERROR"),
        ]
        engine.ingest_to_sqlite(events)

        score = engine.get_24h_risk_score()
        # Should count WARN + ERROR = 2, which is MEDIUM
        assert score == "MEDIUM"

    def test_get_24h_risk_score_ignores_old_events(self, tmp_path):
        """Test get_24h_risk_score ignores events older than 24h.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        old_time = now - timedelta(hours=25)

        events = [
            Event(timestamp=old_time, event="Old error", severity="ERROR"),
            Event(timestamp=old_time, event="Old warning", severity="WARN"),
            Event(timestamp=old_time, event="Old error 2", severity="ERROR"),
        ]
        engine.ingest_to_sqlite(events)

        score = engine.get_24h_risk_score()
        # Should ignore all old events
        assert score == "LOW"

    def test_get_24h_risk_score_includes_recent_events(self, tmp_path):
        """Test get_24h_risk_score includes events from last 24h.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        recent_time = now - timedelta(hours=1)

        events = [
            Event(timestamp=recent_time, event="Recent error", severity="ERROR"),
            Event(timestamp=recent_time, event="Recent warning", severity="WARN"),
        ]
        engine.ingest_to_sqlite(events)

        score = engine.get_24h_risk_score()
        # Should count 2 WARN/ERROR events = MEDIUM
        assert score == "MEDIUM"


class TestGetThreatTimeline:
    """Test get_threat_timeline functionality."""

    def test_get_threat_timeline_no_events(self, tmp_path):
        """Test get_threat_timeline with no events in database.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        timeline = engine.get_threat_timeline(days=7)
        assert timeline == []

    def test_get_threat_timeline_single_event(self, tmp_path):
        """Test get_threat_timeline with a single event.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        event = Event(timestamp=now, event="Test event", severity="ERROR")
        engine.ingest_to_sqlite([event])

        timeline = engine.get_threat_timeline(days=7)
        assert len(timeline) == 1
        assert timeline[0].event == "Test event"

    def test_get_threat_timeline_multiple_events_sorted(self, tmp_path):
        """Test get_threat_timeline returns events sorted by timestamp.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(
                timestamp=now - timedelta(hours=i), event=f"Event {i}", severity="ERROR"
            )
            for i in range(5)
        ]
        # Insert in reverse order
        engine.ingest_to_sqlite(list(reversed(events)))

        timeline = engine.get_threat_timeline(days=7)
        assert len(timeline) == 5
        # Should be sorted by timestamp (oldest first)
        for i in range(len(timeline) - 1):
            assert timeline[i].timestamp <= timeline[i + 1].timestamp

    def test_get_threat_timeline_default_days(self, tmp_path):
        """Test get_threat_timeline uses default days=7.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(timestamp=now - timedelta(days=5), event="Event 5 days old", severity="ERROR"),
            Event(
                timestamp=now - timedelta(days=10), event="Event 10 days old", severity="ERROR"
            ),
        ]
        engine.ingest_to_sqlite(events)

        timeline = engine.get_threat_timeline()  # Default days=7
        # Should include 5-day-old event but not 10-day-old event
        assert len(timeline) == 1
        assert "5 days old" in timeline[0].event

    def test_get_threat_timeline_custom_days(self, tmp_path):
        """Test get_threat_timeline with custom days parameter.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(timestamp=now - timedelta(days=5), event="Event 5 days old", severity="ERROR"),
            Event(
                timestamp=now - timedelta(days=15), event="Event 15 days old", severity="ERROR"
            ),
        ]
        engine.ingest_to_sqlite(events)

        timeline = engine.get_threat_timeline(days=30)
        # Should include both events when days=30
        assert len(timeline) == 2

    def test_get_threat_timeline_ignores_old_events(self, tmp_path):
        """Test get_threat_timeline filters out old events.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(timestamp=now, event="Recent event", severity="ERROR"),
            Event(
                timestamp=now - timedelta(days=10), event="Old event", severity="ERROR"
            ),
        ]
        engine.ingest_to_sqlite(events)

        timeline = engine.get_threat_timeline(days=7)
        assert len(timeline) == 1
        assert "Recent" in timeline[0].event

    def test_get_threat_timeline_all_severities(self, tmp_path):
        """Test get_threat_timeline includes all severity levels.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        now = datetime.now()
        events = [
            Event(timestamp=now, event="Success event", severity="SUCCESS"),
            Event(timestamp=now, event="Warn event", severity="WARN"),
            Event(timestamp=now, event="Error event", severity="ERROR"),
        ]
        engine.ingest_to_sqlite(events)

        timeline = engine.get_threat_timeline(days=7)
        # Should include all events regardless of severity
        assert len(timeline) == 3

    def test_get_threat_timeline_one_day(self, tmp_path):
        """Test get_threat_timeline with days=1 includes last 24 hours.

        Args:
            tmp_path: pytest temp directory fixture
        """
        db_path = tmp_path / "test.db"
        engine = AnalyticsEngine(db_path=db_path)

        # Use fixed times to avoid timing issues
        now = datetime.now()
        recent = now - timedelta(hours=12)
        old = now - timedelta(days=2)

        events = [
            Event(timestamp=recent, event="Recent event", severity="ERROR"),
            Event(timestamp=old, event="Old event", severity="ERROR"),
        ]
        engine.ingest_to_sqlite(events)

        timeline = engine.get_threat_timeline(days=1)
        # Should include recent event within last 1 day, not 2 days old
        assert len(timeline) == 1
        assert "Recent" in timeline[0].event
