"""Configuration management for AI Phone Assistant."""

import os
import re
from typing import Optional, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ConfigDict


# Centralized version - single source of truth
__version__ = "0.1.0"


class Config(BaseModel):
    """Application configuration with validation."""

    model_config = ConfigDict(extra="allow")

    # Anthropic Claude API
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude")

    # Twilio Configuration
    twilio_account_sid: str = Field(..., description="Twilio account SID")
    twilio_auth_token: str = Field(..., description="Twilio auth token")
    twilio_phone_number: str = Field(..., description="Twilio phone number")

    # CRM Integration (optional)
    crm_api_key: Optional[str] = Field(None, description="CRM API key")
    crm_api_url: Optional[str] = Field(None, description="CRM API URL")

    # Application Settings
    debug: bool = Field(False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", description="Logging level"
    )

    # Server Settings
    server_host: str = Field("0.0.0.0", description="Server host")
    server_port: int = Field(8000, description="Server port")

    # Voice Settings
    speech_timeout: str = Field("auto", description="Speech timeout setting")
    voice_language: str = Field("en-US", description="Voice recognition language")

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str) -> str:
        """Validate Anthropic API key format."""
        if not v or not v.strip():
            raise ValueError("ANTHROPIC_API_KEY is required and cannot be empty")
        v = v.strip()
        if not v.startswith("sk-ant-"):
            raise ValueError(
                "Invalid Anthropic API key format. Key should start with 'sk-ant-'"
            )
        return v

    @field_validator("twilio_account_sid")
    @classmethod
    def validate_twilio_sid(cls, v: str) -> str:
        """Validate Twilio Account SID format."""
        if not v or not v.strip():
            raise ValueError("TWILIO_ACCOUNT_SID is required and cannot be empty")
        v = v.strip()
        if not v.startswith("AC"):
            raise ValueError(
                "Invalid Twilio Account SID format. SID should start with 'AC'"
            )
        return v

    @field_validator("twilio_auth_token")
    @classmethod
    def validate_twilio_token(cls, v: str) -> str:
        """Validate Twilio Auth Token is provided."""
        if not v or not v.strip():
            raise ValueError("TWILIO_AUTH_TOKEN is required and cannot be empty")
        return v.strip()

    @field_validator("twilio_phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate Twilio phone number format (E.164)."""
        if not v or not v.strip():
            raise ValueError("TWILIO_PHONE_NUMBER is required and cannot be empty")
        v = v.strip()
        # E.164 format: + followed by 1-15 digits
        if not re.match(r"^\+[1-9]\d{1,14}$", v):
            raise ValueError(
                "Invalid phone number format. Use E.164 format (e.g., +14155551234)"
            )
        return v


def load_config() -> Config:
    """
    Load configuration from environment variables.

    Returns:
        Config: Application configuration object

    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    # Load .env file if it exists
    load_dotenv()

    # Create config from environment variables
    config_dict = {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "twilio_phone_number": os.getenv("TWILIO_PHONE_NUMBER", ""),
        "crm_api_key": os.getenv("CRM_API_KEY"),
        "crm_api_url": os.getenv("CRM_API_URL"),
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
        "server_host": os.getenv("SERVER_HOST", "0.0.0.0"),
        "server_port": int(os.getenv("SERVER_PORT", "8000")),
        "speech_timeout": os.getenv("SPEECH_TIMEOUT", "auto"),
        "voice_language": os.getenv("VOICE_LANGUAGE", "en-US"),
    }

    try:
        return Config(**config_dict)
    except Exception as e:
        raise ValueError(f"Configuration error: {e}")


def mask_phone_number(phone: str) -> str:
    """
    Mask a phone number for safe logging.

    Args:
        phone: Phone number to mask

    Returns:
        Masked phone number (e.g., +1***5678)
    """
    if not phone or len(phone) < 4:
        return "***"
    return phone[:2] + "*" * (len(phone) - 6) + phone[-4:]


def mask_sensitive_string(value: str, visible_chars: int = 4) -> str:
    """
    Mask a sensitive string for safe logging.

    Args:
        value: String to mask
        visible_chars: Number of characters to show at the end

    Returns:
        Masked string
    """
    if not value or len(value) <= visible_chars:
        return "***"
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]
