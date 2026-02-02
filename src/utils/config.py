"""Configuration management for AI Phone Assistant."""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Application configuration."""

    # Anthropic Claude API (optional - can run with just Ollama)
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key for Claude")

    # Ollama Configuration (local AI server)
    ollama_url: str = Field("http://192.168.0.234:11434", description="Ollama API base URL")
    ollama_default_model: str = Field(
        "quick-responder:latest", description="Default Ollama model for fast responses"
    )
    ollama_smart_model: str = Field("llama3.3:70b", description="Ollama model for complex queries")
    ollama_chat_model: str = Field(
        "cyberque-chat:latest", description="Ollama model for general chat"
    )

    # AI Gateway Configuration (Cloudflare Workers AI)
    ai_gateway_url: str = Field("https://ai-gateway.aiqso.io", description="AIQSO AI Gateway URL")
    ai_gateway_default_model: str = Field(
        "auto", description="AI Gateway default model (auto for smart routing)"
    )
    ai_gateway_enabled: bool = Field(True, description="Enable AI Gateway as a backend option")

    # AI Routing Configuration
    prefer_local_ai: bool = Field(
        True, description="Prefer local Ollama over Claude when quality is similar"
    )
    prefer_edge_ai: bool = Field(
        False, description="Prefer edge AI Gateway over local Ollama for simple queries"
    )
    ai_timeout: float = Field(30.0, description="Timeout for AI requests in seconds")

    # Twilio Configuration
    twilio_account_sid: str = Field(..., description="Twilio account SID")
    twilio_auth_token: str = Field(..., description="Twilio auth token")
    twilio_phone_number: str = Field(..., description="Twilio phone number")

    # CRM Integration (optional)
    crm_api_key: Optional[str] = Field(None, description="CRM API key")
    crm_api_url: Optional[str] = Field(None, description="CRM API URL")

    # Calendar Integration (optional)
    google_calendar_credentials: Optional[str] = Field(
        None, description="Path to Google Calendar credentials JSON"
    )
    calendar_id: Optional[str] = Field(None, description="Google Calendar ID for appointments")

    # Application Settings
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")

    # Business Configuration
    business_name: Optional[str] = Field(None, description="Business name for greetings")
    business_type: Optional[str] = Field(
        None, description="Business type (auto_shop, salon, medical, general)"
    )
    business_hours: Optional[str] = Field(
        None, description="Business hours (e.g., 'Mon-Fri 9am-5pm')"
    )

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
        # Claude API (optional)
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY") or None,
        # Ollama Configuration
        "ollama_url": os.getenv("OLLAMA_URL", "http://192.168.0.234:11434"),
        "ollama_default_model": os.getenv("OLLAMA_DEFAULT_MODEL", "quick-responder:latest"),
        "ollama_smart_model": os.getenv("OLLAMA_SMART_MODEL", "llama3.3:70b"),
        "ollama_chat_model": os.getenv("OLLAMA_CHAT_MODEL", "cyberque-chat:latest"),
        # AI Gateway
        "ai_gateway_url": os.getenv("AI_GATEWAY_URL", "https://ai-gateway.aiqso.io"),
        "ai_gateway_default_model": os.getenv("AI_GATEWAY_MODEL", "auto"),
        "ai_gateway_enabled": os.getenv("AI_GATEWAY_ENABLED", "true").lower() == "true",
        # AI Routing
        "prefer_local_ai": os.getenv("PREFER_LOCAL_AI", "true").lower() == "true",
        "prefer_edge_ai": os.getenv("PREFER_EDGE_AI", "false").lower() == "true",
        "ai_timeout": float(os.getenv("AI_TIMEOUT", "30.0")),
        # Twilio
        "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "twilio_phone_number": os.getenv("TWILIO_PHONE_NUMBER", ""),
        # CRM
        "crm_api_key": os.getenv("CRM_API_KEY"),
        "crm_api_url": os.getenv("CRM_API_URL"),
        # Calendar
        "google_calendar_credentials": os.getenv("GOOGLE_CALENDAR_CREDENTIALS"),
        "calendar_id": os.getenv("CALENDAR_ID"),
        # Application
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        # Business
        "business_name": os.getenv("BUSINESS_NAME"),
        "business_type": os.getenv("BUSINESS_TYPE"),
        "business_hours": os.getenv("BUSINESS_HOURS"),
    }

    try:
        return Config(**config_dict)
    except Exception as e:
        raise ValueError(f"Failed to load configuration: {e}") from e
