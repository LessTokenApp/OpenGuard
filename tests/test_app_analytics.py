"""Tests for event persistence through the application.

The app collects events in a session list for the UI, but nothing was writing
them to disk. AnalyticsEngine exists but was never instantiated, so all events
were lost when the app closed.
"""



from src.core.analytics_engine import AnalyticsEngine


class TestAnalyticsPersistence:
    """Events logged in the app must survive restart."""

    def test_analytics_engine_is_created(self, qapp):
        """The app must instantiate the engine at startup."""
        qapp.setup_ui()

        assert isinstance(qapp.analytics_engine, AnalyticsEngine)

    def test_events_are_written_to_the_engine(self, qapp):
        """Logged activity must go to both the UI and the persistent store."""
        qapp.setup_ui()
        qapp.analytics_engine.events.clear()

        qapp._log("test event", "SUCCESS")

        assert len(qapp.analytics_engine.events) == 1
        assert qapp.analytics_engine.events[0].event == "test event"

    def test_engine_persists_events_to_disk(self, qapp, tmp_path):
        """Closing the app must write events to the configured JSONL path."""
        qapp.setup_ui()
        log_file = tmp_path / "events.jsonl"
        qapp.analytics_engine.log_file = str(log_file)
        qapp.analytics_engine.events.clear()

        qapp._log("persisted event", "SUCCESS")
        qapp.analytics_engine.save_events()

        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        assert "persisted event" in lines[0]
