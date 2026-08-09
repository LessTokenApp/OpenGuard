"""Tests for UI styles and dark mode functionality."""

import pytest
from PyQt6.QtWidgets import QMainWindow, QDialog, QWizard

from src.ui.styles import (
    COLOR_SAFE,
    COLOR_WARN,
    COLOR_ERROR,
    get_stylesheet,
)
from src.ui.main_window import MainWindow
from src.ui.settings_dialog import SettingsDialog
from src.ui.onboarding_wizard import OnboardingWizard
from src.ui.analytics_modal import AnalyticsModal


class TestColorConstants:
    """Test that color constants are defined with correct hex values."""

    def test_color_safe_constant_exists(self):
        """Test that COLOR_SAFE constant is defined."""
        assert COLOR_SAFE is not None

    def test_color_safe_value(self):
        """Test that COLOR_SAFE has correct hex value."""
        assert COLOR_SAFE == "#22C55E"

    def test_color_warn_constant_exists(self):
        """Test that COLOR_WARN constant is defined."""
        assert COLOR_WARN is not None

    def test_color_warn_value(self):
        """Test that COLOR_WARN has correct hex value."""
        assert COLOR_WARN == "#EAB308"

    def test_color_error_constant_exists(self):
        """Test that COLOR_ERROR constant is defined."""
        assert COLOR_ERROR is not None

    def test_color_error_value(self):
        """Test that COLOR_ERROR has correct hex value."""
        assert COLOR_ERROR == "#EF4444"


class TestGetStylesheet:
    """Test the get_stylesheet function."""

    def test_get_stylesheet_returns_string(self):
        """Test that get_stylesheet returns a string."""
        result = get_stylesheet()
        assert isinstance(result, str)

    def test_get_stylesheet_returns_non_empty_string(self):
        """Test that get_stylesheet returns a non-empty string."""
        result = get_stylesheet()
        assert len(result) > 0

    def test_get_stylesheet_dark_mode_default(self):
        """Test that get_stylesheet uses dark mode by default."""
        result = get_stylesheet()
        # Dark mode should contain dark background color
        assert "#1F2937" in result

    def test_get_stylesheet_dark_mode_explicit(self):
        """Test that get_stylesheet with dark_mode=True returns dark theme."""
        result = get_stylesheet(dark_mode=True)
        # Should contain dark background color
        assert "#1F2937" in result

    def test_get_stylesheet_light_mode(self):
        """Test that get_stylesheet with dark_mode=False returns light theme."""
        result = get_stylesheet(dark_mode=False)
        # Should contain light background color
        assert "#FFFFFF" in result

    def test_get_stylesheet_dark_vs_light_different(self):
        """Test that dark and light mode produce different stylesheets."""
        dark = get_stylesheet(dark_mode=True)
        light = get_stylesheet(dark_mode=False)
        assert dark != light

    def test_get_stylesheet_contains_button_styles(self):
        """Test that stylesheet contains button styles."""
        result = get_stylesheet()
        assert "QPushButton" in result

    def test_get_stylesheet_contains_label_styles(self):
        """Test that stylesheet contains label styles."""
        result = get_stylesheet()
        assert "QLabel" in result

    def test_get_stylesheet_contains_textedit_styles(self):
        """Test that stylesheet contains text edit styles."""
        result = get_stylesheet()
        assert "QTextEdit" in result

    def test_get_stylesheet_contains_groupbox_styles(self):
        """Test that stylesheet contains group box styles."""
        result = get_stylesheet()
        assert "QGroupBox" in result

    def test_get_stylesheet_dark_text_color(self):
        """Test that dark mode has light text color."""
        result = get_stylesheet(dark_mode=True)
        # Dark mode text should be light
        assert "#F3F4F6" in result

    def test_get_stylesheet_light_text_color(self):
        """Test that light mode has dark text color."""
        result = get_stylesheet(dark_mode=False)
        # Light mode text should be dark
        assert "#1F2937" in result


class TestMainWindowStylesheet:
    """Test that MainWindow has stylesheet applied."""

    def test_main_window_has_stylesheet(self, qapp):
        """Test that MainWindow has a stylesheet applied.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        assert window.styleSheet() != ""

    def test_main_window_stylesheet_not_empty(self, qapp):
        """Test that MainWindow stylesheet is not empty.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        stylesheet = window.styleSheet()
        assert len(stylesheet) > 0

    def test_main_window_stylesheet_contains_qmainwindow(self, qapp):
        """Test that MainWindow stylesheet contains QMainWindow style.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        window = MainWindow()
        stylesheet = window.styleSheet()
        assert "QMainWindow" in stylesheet


class TestSettingsDialogStylesheet:
    """Test that SettingsDialog has stylesheet applied."""

    def test_settings_dialog_has_stylesheet(self, qapp):
        """Test that SettingsDialog has a stylesheet applied.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        assert dialog.styleSheet() != ""

    def test_settings_dialog_stylesheet_not_empty(self, qapp):
        """Test that SettingsDialog stylesheet is not empty.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        stylesheet = dialog.styleSheet()
        assert len(stylesheet) > 0

    def test_settings_dialog_stylesheet_contains_qdialog(self, qapp):
        """Test that SettingsDialog stylesheet contains QDialog style.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        dialog = SettingsDialog()
        stylesheet = dialog.styleSheet()
        assert "QDialog" in stylesheet


class TestOnboardingWizardStylesheet:
    """Test that OnboardingWizard has stylesheet applied."""

    def test_onboarding_wizard_has_stylesheet(self, qapp):
        """Test that OnboardingWizard has a stylesheet applied.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        assert wizard.styleSheet() != ""

    def test_onboarding_wizard_stylesheet_not_empty(self, qapp):
        """Test that OnboardingWizard stylesheet is not empty.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        stylesheet = wizard.styleSheet()
        assert len(stylesheet) > 0

    def test_onboarding_wizard_stylesheet_contains_qwizard(self, qapp):
        """Test that OnboardingWizard stylesheet contains QWizard/QDialog style.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        wizard = OnboardingWizard()
        stylesheet = wizard.styleSheet()
        # QWizard inherits from QDialog, so should have QDialog style
        assert "QDialog" in stylesheet


class TestAnalyticsModalStylesheet:
    """Test that AnalyticsModal has stylesheet applied."""

    def test_analytics_modal_has_stylesheet(self, qapp):
        """Test that AnalyticsModal has a stylesheet applied.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal()
        assert modal.styleSheet() != ""

    def test_analytics_modal_stylesheet_not_empty(self, qapp):
        """Test that AnalyticsModal stylesheet is not empty.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal()
        stylesheet = modal.styleSheet()
        assert len(stylesheet) > 0

    def test_analytics_modal_stylesheet_contains_qdialog(self, qapp):
        """Test that AnalyticsModal stylesheet contains QDialog style.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal()
        stylesheet = modal.styleSheet()
        assert "QDialog" in stylesheet

    def test_analytics_modal_pro_has_stylesheet(self, qapp):
        """Test that AnalyticsModal with is_pro=True has stylesheet.

        Args:
            qapp: pytest-qt fixture for QApplication
        """
        modal = AnalyticsModal(is_pro=True)
        assert modal.styleSheet() != ""


class TestStylesheetContent:
    """Test specific content in the generated stylesheet."""

    def test_stylesheet_has_dark_background_dark_mode(self):
        """Test that dark mode stylesheet contains dark background."""
        result = get_stylesheet(dark_mode=True)
        assert "#1F2937" in result

    def test_stylesheet_has_light_background_light_mode(self):
        """Test that light mode stylesheet contains light background."""
        result = get_stylesheet(dark_mode=False)
        assert "#FFFFFF" in result

    def test_stylesheet_contains_button_color(self):
        """Test that stylesheet contains button color."""
        result = get_stylesheet()
        assert "#3B82F6" in result

    def test_stylesheet_contains_hover_color(self):
        """Test that stylesheet contains hover button color."""
        result = get_stylesheet()
        assert "#2563EB" in result

    def test_stylesheet_dark_border_color_dark_mode(self):
        """Test that dark mode has appropriate border color."""
        result = get_stylesheet(dark_mode=True)
        assert "#374151" in result

    def test_stylesheet_light_border_color_light_mode(self):
        """Test that light mode has appropriate border color."""
        result = get_stylesheet(dark_mode=False)
        assert "#E5E7EB" in result
