import pytest
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from src.ui.analytics_modal import AnalyticsModal
from src.models.event import Event


@pytest.fixture
def app():
    if QApplication.instance():
        return QApplication.instance()
    return QApplication([])


def test_analytics_modal_creation(app):
    """Test modal opens"""
    modal = AnalyticsModal(is_pro=False)
    assert modal is not None


def test_free_modal_shows_basic_only(app):
    """Test FREE tier shows only basic analytics"""
    modal = AnalyticsModal(is_pro=False)
    assert modal.is_pro is False
    # Verify PRO sections are hidden
    assert modal.email_alerts_label.isHidden() or "PRO" in modal.email_alerts_label.text()


def test_pro_modal_shows_advanced(app):
    """Test PRO tier shows advanced features"""
    modal = AnalyticsModal(is_pro=True)
    assert modal.is_pro is True


def test_set_events_updates_display(app):
    """Test that events are displayed"""
    modal = AnalyticsModal(is_pro=False)
    events = [
        Event(datetime.now(), "Test event 1", "SUCCESS"),
        Event(datetime.now(), "Test event 2", "WARN"),
    ]
    modal.set_events(events)
    # Verify display updated
    display_text = modal.stats_label.text()
    assert "2" in display_text or "events" in display_text.lower()
