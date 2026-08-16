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


class TestOnboardingWizardCompletionPage:
    """Test completion page (Screen 4) content and messaging."""

    def test_completion_page_label_does_not_claim_protection_is_on(self, qapp):
        """Test that completion page does NOT falsely claim "protection is now ON".

        This verifies that the completion screen does not make false
        statements about protection being active, since enable_hardening()
        is never called during onboarding.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        completion_page = wizard.page(3)  # Page 4 is index 3

        # Find the label widget
        from PyQt6.QtWidgets import QLabel

        label = None
        for widget in completion_page.findChildren(QLabel):
            label = widget
            break

        assert label is not None, "Completion page should have a label"
        page_text = label.text()

        # Assert false claim is NOT present
        assert "is now ON" not in page_text, (
            "Completion page should NOT claim 'is now ON' "
            "since protection is not actually enabled"
        )

    def test_completion_page_label_mentions_configuration_saved(self, qapp):
        """Test that completion page mentions configuration was saved.

        The completion page should confirm that settings/configuration
        were saved successfully.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        completion_page = wizard.page(3)  # Page 4 is index 3

        # Find the label widget
        from PyQt6.QtWidgets import QLabel

        label = None
        for widget in completion_page.findChildren(QLabel):
            label = widget
            break

        assert label is not None
        page_text = label.text()

        # Assert that configuration/saving is mentioned
        assert "Complete" in page_text or "saved" in page_text.lower(), (
            "Completion page should mention that configuration/settings are complete or saved"
        )

    def test_completion_page_label_mentions_next_steps(self, qapp):
        """Test that completion page tells user what to do next.

        The page should instruct the user on how to enable protection
        (e.g., via the toggle in the main window).

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        completion_page = wizard.page(3)  # Page 4 is index 3

        # Find the label widget
        from PyQt6.QtWidgets import QLabel

        label = None
        for widget in completion_page.findChildren(QLabel):
            label = widget
            break

        assert label is not None
        page_text = label.text()

        # Assert that next steps are mentioned (enable, toggle, open, turn on, etc.)
        lower_text = page_text.lower()
        next_step_keywords = ["enable", "toggle", "open", "turn on", "button"]
        has_next_step = any(keyword in lower_text for keyword in next_step_keywords)
        assert has_next_step, (
            "Completion page should mention how to enable/toggle protection "
            "(e.g., via button, toggle, or opening the main window)"
        )
