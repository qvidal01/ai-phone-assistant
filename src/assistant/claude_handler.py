"""Claude AI conversation handler for phone assistant."""

from typing import List, Dict, Optional
from anthropic import Anthropic
from src.utils.logger import setup_logger


class ClaudeHandler:
    """Handles conversations with Claude AI."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Claude handler.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.logger = setup_logger(__name__)
        self.conversation_history: List[Dict[str, str]] = []

    def generate_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024
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
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Default system prompt for phone assistant
            if system_prompt is None:
                system_prompt = (
                    "You are a helpful phone assistant handling customer inquiries. "
                    "You can help with appointment scheduling, status updates, and "
                    "general questions. Be professional, friendly, and concise in "
                    "your responses as this is a phone conversation. "
                    "Keep responses brief and to the point."
                )

            # Generate response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=self.conversation_history
            )

            # Extract response text
            assistant_message = response.content[0].text

            # Add assistant response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            self.logger.info(f"Generated response for user message: {user_message[:50]}...")
            return assistant_message

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble processing that. Could you please repeat?"

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.logger.info("Conversation history reset")

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
                system="You are a helpful assistant that summarizes conversations.",
                messages=self.conversation_history + [{
                    "role": "user",
                    "content": summary_prompt
                }]
            )

            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return "Unable to generate summary."
