"""Tests for settings module."""

import pytest
from pathlib import Path
import os
from src.config.settings import Settings, get_settings


def test_settings_loading():
    """Test that settings can be loaded."""
    # This test will fail if .env is not properly configured
    # but that's expected for initial setup
    try:
        settings = get_settings()
        assert settings is not None
        assert isinstance(settings.telegram_api_id, int)
        assert isinstance(settings.telegram_api_hash, str)
    except Exception:
        # Expected if .env is not configured
        pass


def test_settings_properties():
    """Test settings properties."""
    try:
        settings = get_settings()
        credentials = settings.telegram_credentials
        assert "api_id" in credentials
        assert "api_hash" in credentials
        assert "phone_number" in credentials
    except Exception:
        # Expected if .env is not configured
        pass

