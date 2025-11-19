"""Configuration management for AI Phone Assistant."""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Application configuration."""

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
    log_level: str = Field("INFO", description="Logging level")

    class Config:
        """Pydantic configuration."""
        extra = "allow"


def load_config() -> Config:
    """
    Load configuration from environment variables.

    Returns:
        Config: Application configuration object

    Raises:
        ValueError: If required environment variables are missing
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
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }

    try:
        return Config(**config_dict)
    except Exception as e:
        raise ValueError(f"Failed to load configuration: {e}")
