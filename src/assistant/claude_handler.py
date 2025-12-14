"""Claude AI conversation handler for phone assistant."""

from typing import List, Dict, Optional
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError
from src.utils.logger import setup_logger


# Default configuration
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 1024
MAX_CONVERSATION_LENGTH = 50  # Prevent unbounded memory growth


class ClaudeHandler:
    """Handles conversations with Claude AI."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        log_level: str = "INFO"
    ):
        """
        Initialize Claude handler.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            log_level: Logging level
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.logger = setup_logger(__name__, level=log_level)
        self.conversation_history: List[Dict[str, str]] = []
        self._default_system_prompt = (
            "You are a helpful phone assistant handling customer inquiries. "
            "You can help with appointment scheduling, status updates, and "
            "general questions. Be professional, friendly, and concise in "
            "your responses as this is a phone conversation. "
            "Keep responses brief and to the point."
        )

    def generate_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ) -> str:
        """
        Generate a response from Claude based on user input.

        Args:
            user_message: The user's message
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens in response

        Returns:
            str: Claude's response
        """
        try:
            # Validate input
            if not user_message or not user_message.strip():
                return "I didn't catch that. Could you please repeat?"

            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message.strip()
            })

            # Trim conversation history if too long
            self._trim_conversation_history()

            # Use provided system prompt or default
            effective_prompt = system_prompt or self._default_system_prompt

            # Generate response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=effective_prompt,
                messages=self.conversation_history
            )

            # Extract response text
            if response.content and len(response.content) > 0:
                assistant_message = response.content[0].text
            else:
                self.logger.warning("Empty response from Claude")
                assistant_message = "I'm sorry, I didn't generate a proper response. Could you please repeat?"

            # Add assistant response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            # Log truncated message for readability
            truncated_message = user_message[:50] + "..." if len(user_message) > 50 else user_message
            self.logger.debug(f"Generated response for: {truncated_message}")

            return assistant_message

        except RateLimitError as e:
            self.logger.error(f"Rate limit exceeded: {e}")
            self._rollback_user_message()
            return "I'm currently experiencing high demand. Please try again in a moment."

        except APIConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            self._rollback_user_message()
            return "I'm having connection issues. Please try again."

        except APIError as e:
            self.logger.error(f"API error: {e}")
            self._rollback_user_message()
            return "I apologize, but I'm having trouble processing that. Could you please repeat?"

        except Exception as e:
            self.logger.error(f"Unexpected error generating response: {e}")
            self._rollback_user_message()
            return "I apologize, but I'm having trouble processing that. Could you please repeat?"

    def _rollback_user_message(self) -> None:
        """Remove the last user message if an error occurred."""
        if self.conversation_history and self.conversation_history[-1]["role"] == "user":
            self.conversation_history.pop()

    def _trim_conversation_history(self) -> None:
        """Trim conversation history to prevent unbounded growth."""
        if len(self.conversation_history) > MAX_CONVERSATION_LENGTH:
            # Keep recent messages, removing oldest pairs
            excess = len(self.conversation_history) - MAX_CONVERSATION_LENGTH
            self.conversation_history = self.conversation_history[excess:]
            self.logger.debug(f"Trimmed conversation history by {excess} messages")

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self.conversation_history = []
        self.logger.debug("Conversation history reset")

    def get_conversation_summary(self) -> str:
        """
        Get a summary of the current conversation.

        Returns:
            str: Conversation summary
        """
        if not self.conversation_history:
            return "No conversation history."

        try:
            summary_prompt = (
                "Please provide a brief summary of this conversation, "
                "including any key points, decisions, or action items."
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system="You are a helpful assistant that summarizes conversations concisely.",
                messages=self.conversation_history + [{
                    "role": "user",
                    "content": summary_prompt
                }]
            )

            if response.content and len(response.content) > 0:
                return response.content[0].text
            return "Unable to generate summary."

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return "Unable to generate summary."

    def get_conversation_length(self) -> int:
        """Get the current conversation length."""
        return len(self.conversation_history)
