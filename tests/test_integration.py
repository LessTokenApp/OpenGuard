"""Integration tests for OpenGuard E2E workflows.

This module contains end-to-end integration tests that verify complete workflows:
1. User clicks toggle → HardeningManager.enable() → Status updates → Activity log appends
2. AnalyticsEngine reads events → ingest_to_sqlite → get_24h_risk_score works
3. ConfigManager load/save Settings integrated with SettingsDialog
"""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.core.analytics_engine import AnalyticsEngine
from src.core.config_manager import ConfigManager
from src.core.hardening_manager import HardeningManager
from src.models.event import Event
from src.models.settings import Settings
from src.ui.main_window import MainWindow
from src.ui.settings_dialog import SettingsDialog

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_data_dir():
    """Provide a temporary directory for test data.

    Yields:
        Path: Temporary directory path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_file(temp_data_dir):
    """Provide a temporary config file path.

    Args:
        temp_data_dir: Temporary directory fixture

    Yields:
        Path: Path to temporary config file
    """
    config_file = temp_data_dir / "config.yaml"
    yield config_file


@pytest.fixture
def temp_db_file(temp_data_dir):
    """Provide a temporary database file path.

    Args:
        temp_data_dir: Temporary directory fixture

    Yields:
        Path: Path to temporary database file
    """
    db_file = temp_data_dir / "test.db"
    yield db_file


@pytest.fixture
def temp_jsonl_file(temp_data_dir):
    """Provide a temporary JSONL file path.

    Args:
        temp_data_dir: Temporary directory fixture

    Yields:
        Path: Path to temporary JSONL file
    """
    jsonl_file = temp_data_dir / "events.jsonl"
    yield jsonl_file


@pytest.fixture
def sample_events():
    """Provide sample Event objects for testing.

    Returns:
        list: List of Event objects with various severities
    """
    now = datetime.now()
    events = [
        Event(
            timestamp=now,
            event="System protection enabled",
            severity="SUCCESS",
            category="Protection",
        ),
        Event(
            timestamp=now - timedelta(hours=1),
            event="Suspicious process detected",
            severity="WARN",
            category="Threat",
        ),
        Event(
            timestamp=now - timedelta(hours=2),
            event="Network intrusion attempt",
            severity="ERROR",
            category="Security",
        ),
        Event(
            timestamp=now - timedelta(hours=3),
            event="Firewall rule updated",
            severity="SUCCESS",
            category="Configuration",
        ),
        Event(
            timestamp=now - timedelta(hours=5),
            event="Malware signature updated",
            severity="SUCCESS",
            category="Updates",
        ),
    ]
    return events


# ============================================================================
# Integration Test 1: Toggle Protection Workflow
# ============================================================================


class TestToggleProtectionWorkflow:
    """Test complete workflow: Toggle → HardeningManager → Status → Activity Log.

    Workflow:
    1. User clicks toggle button
    2. HardeningManager.enable() is called
    3. Status label is updated
    4. Activity log entry is appended
    """

    @patch("src.core.hardening_manager.subprocess.run")
    def test_enable_protection_full_workflow(self, mock_run, qapp, qtbot):
        """Test complete enable protection workflow.

        Verifies:
        - Toggle button click triggers hardening enable
        - Status changes to protected
        - Activity log is updated
        - Signal is emitted

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for signal testing
        """
        # Setup mock subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Create HardeningManager and MainWindow
        hardening_mgr = HardeningManager()
        main_window = MainWindow()

        # Verify initial state
        assert hardening_mgr.is_protected is False
        assert main_window.is_protected is True  # Default state

        # Set initial status to unprotected
        main_window.set_protection_status(False)
        assert "UNPROTECTED" in main_window.status_label.toPlainText()

        # Connect signals
        status_changed_signal_emitted = []

        def on_status_changed(is_protected):
            status_changed_signal_emitted.append(is_protected)
            main_window.set_protection_status(is_protected)
            # Add log entry
            main_window.add_activity_log_entry(
                Event(
                    timestamp=datetime.now(),
                    event="System protection enabled",
                    severity="SUCCESS",
                    category="Protection",
                )
            )

        hardening_mgr.status_changed.connect(on_status_changed)

        # Trigger enable
        result = hardening_mgr.enable_hardening(level="Moderate")

        # Assertions
        assert result is True
        assert hardening_mgr.get_status() is True
        assert len(status_changed_signal_emitted) == 1
        assert status_changed_signal_emitted[0] is True
        assert "PROTECTED" in main_window.status_label.toPlainText()
        assert "System protection enabled" in main_window.activity_log.toPlainText()

    @patch("src.core.hardening_manager.subprocess.run")
    def test_disable_protection_full_workflow(self, mock_run, qapp, qtbot):
        """Test complete disable protection workflow.

        Verifies:
        - Toggle button click triggers hardening disable
        - Status changes to unprotected
        - Activity log is updated
        - Signal is emitted

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for signal testing
        """
        # Setup mock subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Create HardeningManager and MainWindow
        hardening_mgr = HardeningManager()
        main_window = MainWindow()

        # Set initial state to protected
        hardening_mgr.is_protected = True
        main_window.set_protection_status(True)
        assert "PROTECTED" in main_window.status_label.toPlainText()

        # Connect signals
        status_changed_signal_emitted = []

        def on_status_changed(is_protected):
            status_changed_signal_emitted.append(is_protected)
            main_window.set_protection_status(is_protected)
            # Add log entry
            main_window.add_activity_log_entry(
                Event(
                    timestamp=datetime.now(),
                    event="System protection disabled",
                    severity="SUCCESS",
                    category="Protection",
                )
            )

        hardening_mgr.status_changed.connect(on_status_changed)

        # Trigger disable
        result = hardening_mgr.disable_hardening()

        # Assertions
        assert result is True
        assert hardening_mgr.is_protected is False
        assert len(status_changed_signal_emitted) == 1
        assert status_changed_signal_emitted[0] is False
        assert "UNPROTECTED" in main_window.status_label.toPlainText()
        assert "System protection disabled" in main_window.activity_log.toPlainText()

    @patch("src.core.hardening_manager.subprocess.run")
    def test_failed_enable_does_not_update_ui(self, mock_run, qapp):
        """Test failed enable doesn't update status or activity log.

        Verifies:
        - Failed subprocess doesn't change status
        - Activity log is not updated
        - Error signal is emitted

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
        """
        # Setup mock subprocess for failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"
        mock_run.return_value = mock_result

        # Create HardeningManager and MainWindow
        hardening_mgr = HardeningManager()
        main_window = MainWindow()

        initial_status = hardening_mgr.get_status()
        initial_log = main_window.activity_log.toPlainText()

        # Connect to error signal
        error_messages = []

        def on_error(msg):
            error_messages.append(msg)

        hardening_mgr.error_occurred.connect(on_error)

        # Trigger enable (will fail)
        result = hardening_mgr.enable_hardening()

        # Assertions
        assert result is False
        assert hardening_mgr.get_status() == initial_status
        assert main_window.activity_log.toPlainText() == initial_log
        assert len(error_messages) > 0


# ============================================================================
# Integration Test 2: Analytics Engine Workflow
# ============================================================================


class TestAnalyticsEngineWorkflow:
    """Test complete analytics workflow: Read → Ingest → Calculate Risk Score.

    Workflow:
    1. Read events from JSONL file
    2. Ingest events into SQLite database
    3. Calculate 24-hour risk score
    4. Verify results
    """

    def test_read_and_ingest_events_workflow(self, temp_jsonl_file, temp_db_file):
        """Test reading JSONL events and ingesting into database.

        Verifies:
        - Events are read from JSONL
        - Events are inserted into SQLite
        - Database contains correct number of events
        - Event data is preserved

        Args:
            temp_jsonl_file: Temporary JSONL file path
            temp_db_file: Temporary database file path
        """
        # Create sample JSONL file
        now = datetime.now()
        events_data = [
            {
                "timestamp": now.isoformat(),
                "event": "System started",
                "severity": "SUCCESS",
                "category": "Boot",
            },
            {
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "event": "Threat detected",
                "severity": "WARN",
                "category": "Threat",
            },
            {
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "event": "Intrusion attempt",
                "severity": "ERROR",
                "category": "Security",
            },
        ]

        with open(temp_jsonl_file, "w") as f:
            for event_data in events_data:
                f.write(json.dumps(event_data) + "\n")

        # Create AnalyticsEngine and read events
        engine = AnalyticsEngine(db_path=temp_db_file)
        read_events = engine.read_jsonl(str(temp_jsonl_file))

        # Verify read events
        assert len(read_events) == 3
        assert read_events[0].event == "System started"
        assert read_events[1].severity == "WARN"
        assert read_events[2].category == "Security"

        # Ingest events into database
        inserted_count = engine.ingest_to_sqlite(read_events)

        # Verify ingestion
        assert inserted_count == 3

        # Verify database contents
        conn = sqlite3.connect(temp_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        db_count = cursor.fetchone()[0]
        conn.close()

        assert db_count == 3

    def test_read_ingest_and_calculate_risk_score_workflow(self, temp_jsonl_file, temp_db_file):
        """Test complete workflow: read → ingest → calculate risk score.

        Verifies:
        - Risk score is LOW with no recent warnings/errors
        - Risk score is MEDIUM with 1-2 recent warnings/errors
        - Risk score is HIGH with 3+ recent warnings/errors

        Args:
            temp_jsonl_file: Temporary JSONL file path
            temp_db_file: Temporary database file path
        """
        # Create engine
        engine = AnalyticsEngine(db_path=temp_db_file)
        now = datetime.now()

        # Test 1: LOW risk (only SUCCESS events in 24h)
        events_data = [
            {
                "timestamp": now.isoformat(),
                "event": "System started",
                "severity": "SUCCESS",
                "category": "Boot",
            },
            {
                "timestamp": (now - timedelta(hours=12)).isoformat(),
                "event": "Backup completed",
                "severity": "SUCCESS",
                "category": "Backup",
            },
        ]

        with open(temp_jsonl_file, "w") as f:
            for event_data in events_data:
                f.write(json.dumps(event_data) + "\n")

        read_events = engine.read_jsonl(str(temp_jsonl_file))
        engine.ingest_to_sqlite(read_events)

        risk_score = engine.get_24h_risk_score()
        assert risk_score == "LOW"

        # Clear database for next test
        conn = sqlite3.connect(temp_db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events")
        conn.commit()
        conn.close()

        # Test 2: MEDIUM risk (1-2 WARN/ERROR in 24h)
        events_data = [
            {
                "timestamp": now.isoformat(),
                "event": "Suspicious process",
                "severity": "WARN",
                "category": "Threat",
            },
            {
                "timestamp": (now - timedelta(hours=12)).isoformat(),
                "event": "Firewall updated",
                "severity": "SUCCESS",
                "category": "Config",
            },
        ]

        with open(temp_jsonl_file, "w") as f:
            for event_data in events_data:
                f.write(json.dumps(event_data) + "\n")

        read_events = engine.read_jsonl(str(temp_jsonl_file))
        engine.ingest_to_sqlite(read_events)

        risk_score = engine.get_24h_risk_score()
        assert risk_score == "MEDIUM"

        # Clear database for next test
        conn = sqlite3.connect(temp_db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events")
        conn.commit()
        conn.close()

        # Test 3: HIGH risk (3+ WARN/ERROR in 24h)
        events_data = [
            {
                "timestamp": now.isoformat(),
                "event": "Threat 1",
                "severity": "WARN",
                "category": "Threat",
            },
            {
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "event": "Threat 2",
                "severity": "ERROR",
                "category": "Threat",
            },
            {
                "timestamp": (now - timedelta(hours=6)).isoformat(),
                "event": "Threat 3",
                "severity": "ERROR",
                "category": "Threat",
            },
            {
                "timestamp": (now - timedelta(hours=12)).isoformat(),
                "event": "System started",
                "severity": "SUCCESS",
                "category": "Boot",
            },
        ]

        with open(temp_jsonl_file, "w") as f:
            for event_data in events_data:
                f.write(json.dumps(event_data) + "\n")

        read_events = engine.read_jsonl(str(temp_jsonl_file))
        engine.ingest_to_sqlite(read_events)

        risk_score = engine.get_24h_risk_score()
        assert risk_score == "HIGH"

    def test_read_ingest_and_get_timeline_workflow(
        self, temp_jsonl_file, temp_db_file, sample_events
    ):
        """Test complete workflow: read → ingest → get threat timeline.

        Verifies:
        - Events are properly stored with timestamps
        - Timeline retrieval returns events sorted by timestamp
        - Timeline respects day range filter
        - Old events are not included in recent timeline

        Args:
            temp_jsonl_file: Temporary JSONL file path
            temp_db_file: Temporary database file path
            sample_events: Sample Event objects fixture
        """
        # Create engine
        engine = AnalyticsEngine(db_path=temp_db_file)
        now = datetime.now()

        # Create JSONL with sample events
        events_data = []
        for event in sample_events:
            events_data.append(
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event": event.event,
                    "severity": event.severity,
                    "category": event.category,
                }
            )

        # Add an old event (outside 7-day window)
        events_data.append(
            {
                "timestamp": (now - timedelta(days=10)).isoformat(),
                "event": "Old event",
                "severity": "SUCCESS",
                "category": "Archive",
            }
        )

        with open(temp_jsonl_file, "w") as f:
            for event_data in events_data:
                f.write(json.dumps(event_data) + "\n")

        # Read and ingest
        read_events = engine.read_jsonl(str(temp_jsonl_file))
        inserted_count = engine.ingest_to_sqlite(read_events)

        # Verify all events were ingested
        assert inserted_count == len(events_data)

        # Get 7-day timeline
        timeline = engine.get_threat_timeline(days=7)

        # Verify timeline
        assert len(timeline) == len(sample_events)  # Old event should be excluded
        # Verify chronological order
        for i in range(len(timeline) - 1):
            assert timeline[i].timestamp <= timeline[i + 1].timestamp


# ============================================================================
# Integration Test 3: ConfigManager and SettingsDialog Integration
# ============================================================================


class TestConfigManagerSettingsDialogIntegration:
    """Test ConfigManager and SettingsDialog integration.

    Workflow:
    1. Load config from file using ConfigManager
    2. Display config in SettingsDialog
    3. Modify settings in dialog
    4. Save settings back to file using ConfigManager
    5. Verify persistence
    """

    def test_load_and_display_settings_workflow(self, temp_config_file, qapp):
        """Test loading config and displaying in settings dialog.

        Verifies:
        - ConfigManager loads settings from file
        - SettingsDialog displays loaded settings
        - Dialog values match loaded settings

        Args:
            temp_config_file: Temporary config file path
            qapp: pytest-qt fixture for QApplication
        """
        # Create initial config file
        initial_settings = Settings(
            firewall_level="Basic",
            dns_provider="Google",
            dns_enabled=False,
            network_monitoring=True,
            auto_start=False,
            dark_mode=False,
            systray_enabled=True,
            analytics_enabled=False,
            retention_days=30,
            show_daily_tips=False,
        )

        config_mgr = ConfigManager(config_path=temp_config_file)
        config_mgr.save_config(initial_settings)

        # Load config
        loaded_settings = config_mgr.load_config()

        # Verify loaded settings match
        assert loaded_settings.firewall_level == "Basic"
        assert loaded_settings.dns_provider == "Google"
        assert loaded_settings.dns_enabled is False
        assert loaded_settings.network_monitoring is True
        assert loaded_settings.auto_start is False
        assert loaded_settings.dark_mode is False
        assert loaded_settings.retention_days == 30

        # Display in dialog
        dialog = SettingsDialog(initial_settings=loaded_settings)

        # Verify dialog displays correct values
        assert dialog.firewall_combo.currentText() == "Basic"
        assert dialog.dns_combo.currentText() == "Google"
        assert dialog.dns_enabled_check.isChecked() is False
        assert dialog.network_monitoring_check.isChecked() is True
        assert dialog.auto_start_check.isChecked() is False
        assert dialog.dark_mode_check.isChecked() is False
        assert dialog.retention_spin.value() == 30

    def test_modify_and_save_settings_workflow(self, temp_config_file, qapp):
        """Test modifying settings in dialog and saving to file.

        Verifies:
        - Settings can be modified in dialog
        - get_settings() returns modified settings
        - save_config() persists changes
        - Loading file again retrieves saved values

        Args:
            temp_config_file: Temporary config file path
            qapp: pytest-qt fixture for QApplication
        """
        # Create initial settings
        initial_settings = Settings()
        config_mgr = ConfigManager(config_path=temp_config_file)
        config_mgr.save_config(initial_settings)

        # Load and display in dialog
        loaded_settings = config_mgr.load_config()
        dialog = SettingsDialog(initial_settings=loaded_settings)

        # Modify settings
        dialog.firewall_combo.setCurrentText("Relaxed")
        dialog.dns_combo.setCurrentText("Quad9")
        dialog.dns_enabled_check.setChecked(True)
        dialog.retention_spin.setValue(60)
        dialog.dark_mode_check.setChecked(False)

        # Get modified settings from dialog
        modified_settings = dialog.get_settings()

        # Verify modifications
        assert modified_settings.firewall_level == "Relaxed"
        assert modified_settings.dns_provider == "Quad9"
        assert modified_settings.dns_enabled is True
        assert modified_settings.retention_days == 60
        assert modified_settings.dark_mode is False

        # Save to file
        config_mgr.save_config(modified_settings)

        # Load again and verify persistence
        reloaded_settings = config_mgr.load_config()
        assert reloaded_settings.firewall_level == "Relaxed"
        assert reloaded_settings.dns_provider == "Quad9"
        assert reloaded_settings.dns_enabled is True
        assert reloaded_settings.retention_days == 60
        assert reloaded_settings.dark_mode is False

    def test_invalid_settings_fallback_to_defaults(self, temp_config_file, qapp):
        """Test that invalid config file falls back to defaults.

        Verifies:
        - Invalid YAML returns default settings
        - Missing config file returns default settings
        - Corrupted data is handled gracefully

        Args:
            temp_config_file: Temporary config file path
            qapp: pytest-qt fixture for QApplication
        """
        config_mgr = ConfigManager(config_path=temp_config_file)

        # Test 1: Missing file returns defaults
        settings = config_mgr.load_config()
        assert settings.firewall_level == "Moderate"
        assert settings.dns_provider == "Cloudflare"
        assert settings.dark_mode is True

        # Test 2: Invalid YAML returns defaults
        temp_config_file.write_text("invalid: yaml: content: ][")
        settings = config_mgr.load_config()
        assert settings.firewall_level == "Moderate"

        # Test 3: Invalid firewall level returns defaults
        temp_config_file.write_text("firewall_level: InvalidLevel\n")
        settings = config_mgr.load_config()
        assert settings.firewall_level == "Moderate"

    def test_partial_config_file_with_defaults(self, temp_config_file, qapp):
        """Test loading partial config with defaults for missing fields.

        Verifies:
        - Missing fields use default values
        - Provided fields override defaults
        - No errors on partial files

        Args:
            temp_config_file: Temporary config file path
            qapp: pytest-qt fixture for QApplication
        """
        # Create partial config file
        temp_config_file.write_text("""
firewall_level: Basic
dns_provider: Google
""")

        config_mgr = ConfigManager(config_path=temp_config_file)
        settings = config_mgr.load_config()

        # Verify provided values
        assert settings.firewall_level == "Basic"
        assert settings.dns_provider == "Google"

        # Verify defaults for missing values
        assert settings.dns_enabled is True
        assert settings.dark_mode is True
        assert settings.retention_days == 90
        assert settings.auto_start is True


# ============================================================================
# Integration Test 4: Complete End-to-End Workflow
# ============================================================================


class TestCompleteEndToEndWorkflow:
    """Test complete E2E workflow combining all components.

    Workflow:
    1. Load config and display in settings dialog
    2. Modify and save settings
    3. Enable protection via toggle
    4. Record event in activity log
    5. Ingest event into analytics engine
    6. Calculate risk score
    """

    @patch("src.core.hardening_manager.subprocess.run")
    def test_complete_e2e_workflow(
        self,
        mock_run,
        qapp,
        qtbot,
        temp_config_file,
        temp_db_file,
        temp_jsonl_file,
    ):
        """Test complete end-to-end application workflow.

        Verifies all components work together:
        - Config loading/saving
        - Settings dialog interaction
        - Protection toggle with hardening manager
        - Activity logging in main window
        - Analytics event ingestion and scoring

        Args:
            mock_run: Mocked subprocess.run
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt bot for signal testing
            temp_config_file: Temporary config file path
            temp_db_file: Temporary database file path
            temp_jsonl_file: Temporary JSONL file path
        """
        # Setup mock subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Step 1: Load config and display in dialog
        config_mgr = ConfigManager(config_path=temp_config_file)
        initial_settings = Settings(firewall_level="Basic", dark_mode=False)
        config_mgr.save_config(initial_settings)

        loaded_settings = config_mgr.load_config()
        dialog = SettingsDialog(initial_settings=loaded_settings)

        assert dialog.firewall_combo.currentText() == "Basic"
        assert dialog.dark_mode_check.isChecked() is False

        # Step 2: Modify settings in dialog
        dialog.firewall_combo.setCurrentText("Moderate")
        dialog.dark_mode_check.setChecked(True)

        modified_settings = dialog.get_settings()
        assert modified_settings.firewall_level == "Moderate"
        assert modified_settings.dark_mode is True

        # Step 3: Save settings
        config_mgr.save_config(modified_settings)

        # Step 4: Enable protection
        hardening_mgr = HardeningManager()
        main_window = MainWindow()
        main_window.set_protection_status(False)

        status_events = []

        def on_status_changed(is_protected):
            status_events.append(is_protected)
            main_window.set_protection_status(is_protected)
            main_window.add_activity_log_entry(
                Event(
                    timestamp=datetime.now(),
                    event="System protection enabled",
                    severity="SUCCESS",
                    category="Protection",
                )
            )

        hardening_mgr.status_changed.connect(on_status_changed)

        result = hardening_mgr.enable_hardening(level="Moderate")
        assert result is True

        # Step 5: Verify activity log
        assert "System protection enabled" in main_window.activity_log.toPlainText()

        # Step 6: Record event in analytics
        now = datetime.now()
        event_data = {
            "timestamp": now.isoformat(),
            "event": "System protection enabled",
            "severity": "SUCCESS",
            "category": "Protection",
        }

        with open(temp_jsonl_file, "w") as f:
            f.write(json.dumps(event_data) + "\n")

        # Step 7: Ingest into analytics engine
        engine = AnalyticsEngine(db_path=temp_db_file)
        read_events = engine.read_jsonl(str(temp_jsonl_file))
        inserted_count = engine.ingest_to_sqlite(read_events)

        assert inserted_count == 1

        # Step 8: Calculate risk score
        risk_score = engine.get_24h_risk_score()
        assert risk_score == "LOW"  # Only SUCCESS events

        # Final verification: Reload config to ensure persistence
        final_settings = config_mgr.load_config()
        assert final_settings.firewall_level == "Moderate"
        assert final_settings.dark_mode is True
