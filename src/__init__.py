"""AI Phone Assistant package."""

from src.assistant.phone_assistant import PhoneAssistant
from src.utils.config import Config, load_config

__version__ = "0.1.0"
__all__ = ["PhoneAssistant", "Config", "load_config"]
