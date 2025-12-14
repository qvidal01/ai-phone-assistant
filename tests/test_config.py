"""Tests for configuration module."""

import pytest
from pydantic import ValidationError
from src.utils.config import Config, load_config, mask_phone_number, mask_sensitive_string


class TestConfig:
    """Tests for Config model."""

    def test_config_model_valid(self):
        """Test Config model creation with valid data."""
        config = Config(
            anthropic_api_key="sk-ant-test_key_12345",
            twilio_account_sid="ACtest_sid_12345",
            twilio_auth_token="test_token_12345",
            twilio_phone_number="+14155551234"
        )

        assert config.anthropic_api_key == "sk-ant-test_key_12345"
        assert config.twilio_account_sid == "ACtest_sid_12345"
        assert config.twilio_auth_token == "test_token_12345"
        assert config.twilio_phone_number == "+14155551234"
        assert config.debug is False
        assert config.log_level == "INFO"

    def test_config_with_optional_fields(self):
        """Test Config with optional CRM fields."""
        config = Config(
            anthropic_api_key="sk-ant-test_key_12345",
            twilio_account_sid="ACtest_sid_12345",
            twilio_auth_token="test_token_12345",
            twilio_phone_number="+14155551234",
            crm_api_key="crm_key",
            crm_api_url="https://api.crm.com"
        )

        assert config.crm_api_key == "crm_key"
        assert config.crm_api_url == "https://api.crm.com"

    def test_config_with_new_settings(self):
        """Test Config with new server and voice settings."""
        config = Config(
            anthropic_api_key="sk-ant-test_key_12345",
            twilio_account_sid="ACtest_sid_12345",
            twilio_auth_token="test_token_12345",
            twilio_phone_number="+14155551234",
            server_host="127.0.0.1",
            server_port=9000,
            speech_timeout="5",
            voice_language="es-ES"
        )

        assert config.server_host == "127.0.0.1"
        assert config.server_port == 9000
        assert config.speech_timeout == "5"
        assert config.voice_language == "es-ES"

    def test_config_missing_required_field(self):
        """Test that Config raises error for missing required fields."""
        with pytest.raises(ValidationError):
            Config(
                anthropic_api_key="sk-ant-test_key_12345",
                # Missing required fields
            )


class TestConfigValidation:
    """Tests for Config field validation."""

    def test_invalid_anthropic_api_key_format(self):
        """Test that invalid Anthropic API key format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                anthropic_api_key="invalid_key",
                twilio_account_sid="ACtest_sid_12345",
                twilio_auth_token="test_token_12345",
                twilio_phone_number="+14155551234"
            )
        assert "sk-ant-" in str(exc_info.value)

    def test_empty_anthropic_api_key(self):
        """Test that empty Anthropic API key raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                anthropic_api_key="",
                twilio_account_sid="ACtest_sid_12345",
                twilio_auth_token="test_token_12345",
                twilio_phone_number="+14155551234"
            )
        assert "required" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()

    def test_invalid_twilio_account_sid_format(self):
        """Test that invalid Twilio Account SID format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                anthropic_api_key="sk-ant-test_key_12345",
                twilio_account_sid="invalid_sid",
                twilio_auth_token="test_token_12345",
                twilio_phone_number="+14155551234"
            )
        assert "AC" in str(exc_info.value)

    def test_empty_twilio_auth_token(self):
        """Test that empty Twilio auth token raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                anthropic_api_key="sk-ant-test_key_12345",
                twilio_account_sid="ACtest_sid_12345",
                twilio_auth_token="",
                twilio_phone_number="+14155551234"
            )
        assert "required" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()

    def test_invalid_phone_number_format(self):
        """Test that invalid phone number format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                anthropic_api_key="sk-ant-test_key_12345",
                twilio_account_sid="ACtest_sid_12345",
                twilio_auth_token="test_token_12345",
                twilio_phone_number="1234567890"  # Missing + prefix
            )
        assert "E.164" in str(exc_info.value)

    def test_invalid_log_level(self):
        """Test that invalid log level raises error."""
        with pytest.raises(ValidationError):
            Config(
                anthropic_api_key="sk-ant-test_key_12345",
                twilio_account_sid="ACtest_sid_12345",
                twilio_auth_token="test_token_12345",
                twilio_phone_number="+14155551234",
                log_level="INVALID"
            )


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_from_env(self, monkeypatch):
        """Test loading config from environment variables."""
        # Set environment variables with valid formats
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env_key_12345")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACenv_sid_12345")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "env_token_12345")
        monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+14155551234")
        monkeypatch.setenv("DEBUG", "True")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        config = load_config()

        assert config.anthropic_api_key == "sk-ant-env_key_12345"
        assert config.twilio_account_sid == "ACenv_sid_12345"
        assert config.twilio_auth_token == "env_token_12345"
        assert config.twilio_phone_number == "+14155551234"
        assert config.debug is True
        assert config.log_level == "DEBUG"

    def test_load_config_with_server_settings(self, monkeypatch):
        """Test loading config with server settings from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env_key_12345")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACenv_sid_12345")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "env_token_12345")
        monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+14155551234")
        monkeypatch.setenv("SERVER_HOST", "127.0.0.1")
        monkeypatch.setenv("SERVER_PORT", "9000")

        config = load_config()

        assert config.server_host == "127.0.0.1"
        assert config.server_port == 9000

    def test_load_config_missing_required_raises_error(self, monkeypatch):
        """Test that missing required env vars raises error."""
        # Clear all env vars
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
        monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
        monkeypatch.delenv("TWILIO_PHONE_NUMBER", raising=False)

        with pytest.raises(ValueError) as exc_info:
            load_config()
        assert "Configuration error" in str(exc_info.value)


class TestMaskingFunctions:
    """Tests for PII masking functions."""

    def test_mask_phone_number_standard(self):
        """Test masking a standard phone number."""
        result = mask_phone_number("+14155551234")
        # +14155551234 is 12 chars: first 2 (+1), middle 6 masked, last 4 (1234)
        assert result == "+1******1234"
        assert "4155551" not in result

    def test_mask_phone_number_short(self):
        """Test masking a short string."""
        result = mask_phone_number("+12")
        assert result == "***"

    def test_mask_phone_number_empty(self):
        """Test masking empty string."""
        result = mask_phone_number("")
        assert result == "***"

    def test_mask_phone_number_none(self):
        """Test masking None value."""
        result = mask_phone_number(None)
        assert result == "***"

    def test_mask_sensitive_string_standard(self):
        """Test masking a sensitive string."""
        result = mask_sensitive_string("mysecretapikey123", visible_chars=4)
        assert result.endswith("y123")
        assert "mysecret" not in result

    def test_mask_sensitive_string_short(self):
        """Test masking a short string."""
        result = mask_sensitive_string("abc", visible_chars=4)
        assert result == "***"

    def test_mask_sensitive_string_empty(self):
        """Test masking empty string."""
        result = mask_sensitive_string("")
        assert result == "***"

    def test_mask_sensitive_string_custom_visible(self):
        """Test masking with custom visible characters."""
        result = mask_sensitive_string("mysecretapikey123", visible_chars=6)
        assert result.endswith("key123")
