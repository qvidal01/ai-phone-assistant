"""Ollama AI conversation handler for phone assistant."""

from typing import Optional

import httpx

from src.utils.logger import setup_logger


class OllamaHandler:
    """Handles conversations with local Ollama models."""

    def __init__(
        self,
        base_url: str = "http://192.168.0.234:11434",
        default_model: str = "quick-responder:latest",
        timeout: float = 30.0,
    ):
        """
        Initialize Ollama handler.

        Args:
            base_url: Ollama API base URL
            default_model: Default model to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self.logger = setup_logger(__name__)
        self.conversation_history: list[dict[str, str]] = []

        # Available models for different use cases
        self.models = {
            "fast": "quick-responder:latest",  # 3.2B - fastest responses
            "general": "general-assistant:latest",  # 7.2B - balanced
            "smart": "llama3.3:70b",  # 70B - best quality
            "chat": "cyberque-chat:latest",  # 7.6B - custom fine-tuned
        }

    async def check_health(self) -> bool:
        """
        Check if Ollama server is healthy.

        Returns:
            bool: True if server is reachable
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {e}")
            return False

    def check_health_sync(self) -> bool:
        """
        Synchronous health check for Ollama server.

        Returns:
            bool: True if server is reachable
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {e}")
            return False

    def generate_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 512,
    ) -> str:
        """
        Generate a response from Ollama based on user input.

        Args:
            user_message: The user's message
            system_prompt: Optional system prompt for context
            model: Model to use (defaults to default_model)
            max_tokens: Maximum tokens in response

        Returns:
            str: Ollama's response
        """
        try:
            model = model or self.default_model

            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Default system prompt for phone assistant
            if system_prompt is None:
                system_prompt = (
                    "You are a helpful phone assistant handling customer inquiries. "
                    "You can help with appointment scheduling, status updates, and "
                    "general questions. Be professional, friendly, and concise in "
                    "your responses as this is a phone conversation. "
                    "Keep responses brief - under 2 sentences when possible."
                )

            # Build messages for Ollama chat API
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.conversation_history)

            # Make request to Ollama
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.7,
                        },
                    },
                )
                response.raise_for_status()

                result = response.json()
                assistant_message = result.get("message", {}).get("content", "")

            # Add assistant response to conversation history
            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            self.logger.info(f"Generated response using {model} for: {user_message[:50]}...")
            return assistant_message

        except httpx.TimeoutException:
            self.logger.error("Ollama request timed out")
            return ""
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return ""

    async def generate_response_async(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 512,
    ) -> str:
        """
        Async version of generate_response.

        Args:
            user_message: The user's message
            system_prompt: Optional system prompt for context
            model: Model to use (defaults to default_model)
            max_tokens: Maximum tokens in response

        Returns:
            str: Ollama's response
        """
        try:
            model = model or self.default_model

            self.conversation_history.append({"role": "user", "content": user_message})

            if system_prompt is None:
                system_prompt = (
                    "You are a helpful phone assistant handling customer inquiries. "
                    "You can help with appointment scheduling, status updates, and "
                    "general questions. Be professional, friendly, and concise in "
                    "your responses as this is a phone conversation. "
                    "Keep responses brief - under 2 sentences when possible."
                )

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.conversation_history)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.7,
                        },
                    },
                )
                response.raise_for_status()

                result = response.json()
                assistant_message = result.get("message", {}).get("content", "")

            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            self.logger.info(f"Generated async response using {model}")
            return assistant_message

        except httpx.TimeoutException:
            self.logger.error("Ollama async request timed out")
            return ""
        except Exception as e:
            self.logger.error(f"Error generating async response: {e}")
            return ""

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.logger.info("Conversation history reset")

    def get_conversation_summary(self) -> str:
        """
        Get a summary of the current conversation using Ollama.

        Returns:
            str: Conversation summary
        """
        if not self.conversation_history:
            return "No conversation history."

        try:
            # Use quick model for summarization
            summary_messages = self.conversation_history + [
                {
                    "role": "user",
                    "content": "Please provide a brief 1-2 sentence summary of this conversation.",
                }
            ]

            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.models["fast"],
                        "messages": summary_messages,
                        "stream": False,
                        "options": {"num_predict": 256},
                    },
                )
                response.raise_for_status()

                result = response.json()
                return result.get("message", {}).get("content", "Unable to generate summary.")

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return "Unable to generate summary."

    def get_model_for_task(self, task_type: str) -> str:
        """
        Get the appropriate model for a specific task.

        Args:
            task_type: Type of task (fast, general, smart, chat)

        Returns:
            str: Model name
        """
        return self.models.get(task_type, self.default_model)
