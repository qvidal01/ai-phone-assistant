"""AI Phone Assistant package."""

from src.assistant.phone_assistant import PhoneAssistant
from src.utils.config import Config, load_config, __version__

__all__ = ["PhoneAssistant", "Config", "load_config", "__version__"]
