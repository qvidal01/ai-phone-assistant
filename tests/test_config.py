"""Tests for configuration module."""

import pytest

from src.utils.config import Config, load_config


def test_config_model():
    """Test Config model creation."""
    config = Config(
        anthropic_api_key="test_key",
        twilio_account_sid="test_sid",
        twilio_auth_token="test_token",
        twilio_phone_number="+1234567890",
    )

    assert config.anthropic_api_key == "test_key"
    assert config.twilio_account_sid == "test_sid"
    assert config.twilio_auth_token == "test_token"
    assert config.twilio_phone_number == "+1234567890"
    assert config.debug is False
    assert config.log_level == "INFO"


def test_config_with_optional_fields():
    """Test Config with optional CRM fields."""
    config = Config(
        anthropic_api_key="test_key",
        twilio_account_sid="test_sid",
        twilio_auth_token="test_token",
        twilio_phone_number="+1234567890",
        crm_api_key="crm_key",
        crm_api_url="https://api.crm.com",
    )

    assert config.crm_api_key == "crm_key"
    assert config.crm_api_url == "https://api.crm.com"


def test_config_missing_required_field():
    """Test that Config raises error for missing required fields."""
    with pytest.raises((TypeError, ValueError)):
        Config(
            anthropic_api_key="test_key",
            # Missing required fields
        )


def test_load_config_from_env(monkeypatch):
    """Test loading config from environment variables."""
    # Set environment variables
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env_key")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "env_sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "env_token")
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+1234567890")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    config = load_config()

    assert config.anthropic_api_key == "env_key"
    assert config.twilio_account_sid == "env_sid"
    assert config.twilio_auth_token == "env_token"
    assert config.twilio_phone_number == "+1234567890"
    assert config.debug is True
    assert config.log_level == "DEBUG"
