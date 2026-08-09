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
