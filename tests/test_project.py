"""Smoke tests for the project foundation (Module 0).

These tests verify only that the project scaffold is wired together
correctly: the package imports without error, configuration and
logging initialize successfully, and the main entry point executes
without raising.
"""

import importlib

from app.core.config import get_settings
from app.core.logger import configure_logging
from app.main import main


def test_app_package_imports() -> None:
    """The top-level ``app`` package should import without error."""
    module = importlib.import_module("app")
    assert module is not None


def test_settings_load_successfully() -> None:
    """Application settings should load with valid default values."""
    settings = get_settings()
    assert settings.app_name != ""
    assert settings.log_level != ""


def test_logging_configures_without_error() -> None:
    """Logging configuration should complete without raising."""
    configure_logging()


def test_main_executes_without_error(capsys) -> None:
    """The main entry point should run and print the startup message."""
    main()
    captured = capsys.readouterr()
    assert "AI Consulting Firm initialized successfully." in captured.out
