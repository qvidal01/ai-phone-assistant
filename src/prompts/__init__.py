"""AIQSO prompts module."""

from src.prompts.aiqso_prompts import (
    AIQSO_INFO,
    AIQSO_SERVICES,
    VOICE_SYSTEM_PROMPT,
    SMS_SYSTEM_PROMPT,
    GREETINGS,
    RESPONSES,
    INTENT_PATTERNS,
    get_service_description,
    detect_intent,
    get_contextual_prompt,
)

__all__ = [
    "AIQSO_INFO",
    "AIQSO_SERVICES",
    "VOICE_SYSTEM_PROMPT",
    "SMS_SYSTEM_PROMPT",
    "GREETINGS",
    "RESPONSES",
    "INTENT_PATTERNS",
    "get_service_description",
    "detect_intent",
    "get_contextual_prompt",
]
