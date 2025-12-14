"""Tests for Claude AI handler."""

import pytest
from unittest.mock import MagicMock, patch
from src.assistant.claude_handler import ClaudeHandler, MAX_CONVERSATION_LENGTH


class TestClaudeHandler:
    """Tests for ClaudeHandler class."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client."""
        with patch("src.assistant.claude_handler.Anthropic") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def handler(self, mock_anthropic_client):
        """Create a ClaudeHandler instance with mocked client."""
        return ClaudeHandler(api_key="sk-ant-test_key_12345")

    def test_initialization(self, mock_anthropic_client):
        """Test handler initialization."""
        handler = ClaudeHandler(
            api_key="sk-ant-test_key_12345",
            model="claude-3-opus-20240229"
        )
        assert handler.model == "claude-3-opus-20240229"
        assert handler.conversation_history == []

    def test_generate_response_success(self, handler, mock_anthropic_client):
        """Test successful response generation."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello! How can I help you?")]
        mock_anthropic_client.messages.create.return_value = mock_response

        response = handler.generate_response("Hi there")

        assert response == "Hello! How can I help you?"
        assert len(handler.conversation_history) == 2
        assert handler.conversation_history[0]["role"] == "user"
        assert handler.conversation_history[1]["role"] == "assistant"

    def test_generate_response_empty_input(self, handler, mock_anthropic_client):
        """Test response for empty input."""
        response = handler.generate_response("")
        assert "didn't catch" in response.lower()
        # Should not add to conversation history
        assert len(handler.conversation_history) == 0

    def test_generate_response_whitespace_input(self, handler, mock_anthropic_client):
        """Test response for whitespace-only input."""
        response = handler.generate_response("   ")
        assert "didn't catch" in response.lower()
        assert len(handler.conversation_history) == 0

    def test_generate_response_with_custom_system_prompt(self, handler, mock_anthropic_client):
        """Test response with custom system prompt."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Custom response")]
        mock_anthropic_client.messages.create.return_value = mock_response

        custom_prompt = "You are a helpful sales assistant."
        handler.generate_response("Hello", system_prompt=custom_prompt)

        # Verify the custom prompt was used
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args.kwargs["system"] == custom_prompt

    def test_generate_response_api_error(self, handler, mock_anthropic_client):
        """Test handling of API errors."""
        # Use a generic exception to test error handling
        # (APIError constructor signature varies between versions)
        mock_anthropic_client.messages.create.side_effect = Exception("API Error")

        response = handler.generate_response("Hello")

        assert "trouble processing" in response.lower()
        # User message from failed call should be rolled back
        # (handler starts with empty history, adds "Hello", then rolls it back)
        assert len(handler.conversation_history) == 0

    def test_generate_response_rate_limit(self, handler, mock_anthropic_client):
        """Test handling of rate limit errors."""
        from anthropic import RateLimitError
        mock_anthropic_client.messages.create.side_effect = RateLimitError(
            message="Rate limit",
            response=MagicMock(status_code=429),
            body={}
        )

        response = handler.generate_response("Hello")

        assert "high demand" in response.lower()

    def test_reset_conversation(self, handler, mock_anthropic_client):
        """Test conversation reset."""
        # Add some history
        handler.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        handler.reset_conversation()

        assert handler.conversation_history == []

    def test_conversation_history_trimming(self, handler, mock_anthropic_client):
        """Test that conversation history is trimmed when too long."""
        # Fill up history beyond max
        for i in range(MAX_CONVERSATION_LENGTH + 10):
            handler.conversation_history.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}"
            })

        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_anthropic_client.messages.create.return_value = mock_response

        handler.generate_response("New message")

        # Should be trimmed to max + 2 (new user + assistant)
        assert len(handler.conversation_history) <= MAX_CONVERSATION_LENGTH + 2

    def test_get_conversation_summary_empty(self, handler, mock_anthropic_client):
        """Test summary with empty conversation."""
        summary = handler.get_conversation_summary()
        assert "No conversation history" in summary

    def test_get_conversation_summary_success(self, handler, mock_anthropic_client):
        """Test successful conversation summary."""
        handler.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Summary: Brief greeting exchange.")]
        mock_anthropic_client.messages.create.return_value = mock_response

        summary = handler.get_conversation_summary()

        assert "Summary" in summary

    def test_get_conversation_length(self, handler, mock_anthropic_client):
        """Test getting conversation length."""
        assert handler.get_conversation_length() == 0

        handler.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]

        assert handler.get_conversation_length() == 2
