"""Tests for onboarding wizard UI component."""

import pytest
from PyQt6.QtWidgets import QWizard

from src.models.settings import Settings
from src.ui.onboarding_wizard import OnboardingWizard


class TestOnboardingWizardCreation:
    """Test OnboardingWizard instantiation and basic properties."""

    def test_wizard_creation(self, qapp):
        """Test wizard initializes.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        assert wizard is not None
        assert isinstance(wizard, QWizard)

    def test_wizard_has_four_pages(self, qapp):
        """Test wizard has exactly 4 pages.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        # Verify all 4 pages are accessible
        assert wizard.page(0) is not None
        assert wizard.page(1) is not None
        assert wizard.page(2) is not None
        assert wizard.page(3) is not None

    def test_wizard_window_title(self, qapp):
        """Test wizard has correct window title.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        assert wizard.windowTitle() == "OpenGuard Setup"


class TestOnboardingWizardSettings:
    """Test settings collection and retrieval."""

    def test_wizard_completion_returns_settings(self, qapp):
        """Test that wizard completion returns Settings.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        settings = wizard.get_settings()
        assert isinstance(settings, Settings)

    def test_wizard_default_firewall_level(self, qapp):
        """Test default firewall level is Moderate.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        settings = wizard.get_settings()
        assert settings.firewall_level == "Moderate"

    def test_wizard_firewall_level_basic_selection(self, qapp):
        """Test that Basic firewall level can be selected.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        # Navigate to firewall selection page (page 3, index 2)
        wizard.next()  # Screen 2
        wizard.next()  # Screen 3

        # Find and select Basic radio button
        from PyQt6.QtWidgets import QRadioButton

        for button in wizard.findChildren(QRadioButton):
            if "Basic" in button.text():
                button.setChecked(True)
                break

        settings = wizard.get_settings()
        assert settings.firewall_level == "Basic"

    def test_wizard_firewall_level_relaxed_selection(self, qapp):
        """Test that Relaxed firewall level can be selected.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        # Navigate to firewall selection page (page 3, index 2)
        wizard.next()  # Screen 2
        wizard.next()  # Screen 3

        # Find and select Relaxed radio button
        from PyQt6.QtWidgets import QRadioButton

        for button in wizard.findChildren(QRadioButton):
            if "Relaxed" in button.text():
                button.setChecked(True)
                break

        settings = wizard.get_settings()
        assert settings.firewall_level == "Relaxed"


class TestOnboardingWizardSignals:
    """Test signal emissions from onboarding wizard."""

    def test_wizard_has_completed_signal(self, qapp):
        """Test that wizard has completed signal.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        assert hasattr(wizard, "completed")

    def test_wizard_completed_signal_emits_settings(self, qapp, qtbot):
        """Test that completed signal emits Settings object on accept.

        Args:
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt robot fixture
        """
        wizard = OnboardingWizard()

        with qtbot.waitSignal(wizard.completed, timeout=1000):
            wizard.finished.emit(1)  # Emit finished signal (1 = Accepted)

    def test_wizard_completed_signal_not_emitted_on_cancel(self, qapp, qtbot):
        """Test that completed signal is NOT emitted when wizard is cancelled.

        Args:
            qapp: pytest-qt fixture for QApplication
            qtbot: pytest-qt robot fixture
        """
        wizard = OnboardingWizard()

        with qtbot.assertNotEmitted(wizard.completed, wait=500):
            wizard.finished.emit(0)  # Emit finished signal (0 = Rejected/Cancel)
