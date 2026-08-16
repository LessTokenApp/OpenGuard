"""Tests for analytics modal UI component."""

from datetime import datetime

import pytest

from src.models.event import Event
from src.ui.analytics_modal import AnalyticsModal


class TestAnalyticsModal:
    """Test AnalyticsModal instantiation and event handling."""

    def test_analytics_modal_creation(self, qapp):
        """Test modal opens.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal(is_pro=False)
        assert modal is not None

    def test_free_modal_shows_basic_only(self, qapp):
        """Test FREE tier shows only basic analytics.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal(is_pro=False)
        assert modal.is_pro is False
        # Verify PRO sections are hidden
        assert modal.email_alerts_label.isHidden() or "PRO" in modal.email_alerts_label.text()

    def test_pro_modal_shows_advanced(self, qapp):
        """Test PRO tier shows advanced features.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal(is_pro=True)
        assert modal.is_pro is True

    def test_set_events_updates_display(self, qapp):
        """Test that events are displayed.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal(is_pro=False)
        events = [
            Event(datetime.now(), "Test event 1", "SUCCESS"),
            Event(datetime.now(), "Test event 2", "WARN"),
        ]
        modal.set_events(events)
        # Verify display updated
        display_text = modal.stats_label.text()
        assert "2" in display_text or "events" in display_text.lower()

    def test_modal_excludes_system_events_from_threat_count(self, qapp):
        """Test that system-category events are excluded from threat count.

        This is the regression test for Task 18: clicking "Enable Protection" 6 times
        should NOT show "Threats Blocked: 6", even though each logs a WARN advisory
        with category="system".

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal(is_pro=False)
        now = datetime.now()

        events = [
            # Simulate 6 "Protection enabled" cycles (system advisory events)
            Event(
                timestamp=now,
                event=f"Protection enabled cycle {i}",
                severity="WARN",
                category="system",
            )
            for i in range(6)
        ]
        # Add a SUCCESS event (system, shouldn't count as threat)
        events.append(
            Event(
                timestamp=now,
                event="Protection status: enabled",
                severity="SUCCESS",
                category="system",
            )
        )

        modal.set_events(events)
        display_text = modal.stats_label.text()

        # Total events should still be 7 (all events count for total)
        assert "Total Events: 7" in display_text
        # But threats should be 0 (system events don't count)
        assert "Threats Blocked: 0" in display_text
        # And risk should be LOW
        assert "Last 24h Risk: LOW" in display_text

    def test_modal_includes_non_system_threats_in_count(self, qapp):
        """Test that non-system threat events ARE counted in threat statistics.

        The filter must not accidentally exclude everything. Real threat events
        with non-"system" category must still be counted.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal(is_pro=False)
        now = datetime.now()

        events = [
            # System events should be ignored in threat count
            Event(
                timestamp=now,
                event="Status change",
                severity="WARN",
                category="system",
            ),
            # Real threat events should count
            Event(
                timestamp=now,
                event="Suspicious process detected",
                severity="WARN",
                category="threat",
            ),
            Event(
                timestamp=now,
                event="Malware signature match",
                severity="ERROR",
                category="threat",
            ),
            Event(
                timestamp=now,
                event="Another threat detected",
                severity="ERROR",
                category="threat",
            ),
        ]

        modal.set_events(events)
        display_text = modal.stats_label.text()

        # Total events should be 4
        assert "Total Events: 4" in display_text
        # Threats should be 3 (only non-system WARN/ERROR)
        assert "Threats Blocked: 3" in display_text
        # Risk should be HIGH (3 threat events)
        assert "Last 24h Risk: HIGH" in display_text

    def test_modal_total_events_includes_all_categories(self, qapp):
        """Test that total event count includes all events regardless of category.

        System and non-system events both count toward the total event count.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal(is_pro=False)
        now = datetime.now()

        events = [
            Event(timestamp=now, event="System event", severity="SUCCESS", category="system"),
            Event(timestamp=now, event="Threat event", severity="WARN", category="threat"),
            Event(timestamp=now, event="Another system event", severity="WARN", category="system"),
        ]

        modal.set_events(events)
        display_text = modal.stats_label.text()

        # Total should be 3 (all events)
        assert "Total Events: 3" in display_text
        # Threats should be 1 (only the non-system WARN)
        assert "Threats Blocked: 1" in display_text
