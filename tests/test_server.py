"""Tests for FastAPI server endpoints."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch


# Set up environment variables BEFORE any src imports
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test_key_12345"
os.environ["TWILIO_ACCOUNT_SID"] = "ACtest_sid_12345"
os.environ["TWILIO_AUTH_TOKEN"] = "test_token_12345"
os.environ["TWILIO_PHONE_NUMBER"] = "+14155551234"
os.environ["DEBUG"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def mock_assistant():
    """Create mock PhoneAssistant."""
    assistant = MagicMock()
    assistant.handle_incoming_call.return_value = '<?xml version="1.0"?><Response><Say>Hello!</Say></Response>'
    assistant.process_speech.return_value = '<?xml version="1.0"?><Response><Say>Response</Say></Response>'
    assistant.twilio = MagicMock()
    assistant.twilio.create_response_twiml.return_value = '<?xml version="1.0"?><Response><Say>Error</Say></Response>'
    assistant.claude = MagicMock()
    assistant.claude.generate_response.return_value = "SMS response"
    assistant.send_sms_notification.return_value = "SM12345"
    return assistant


@pytest.fixture
def client(mock_assistant):
    """Create test client with mocked dependencies."""
    # Patch handlers to prevent actual API connections
    with patch("src.assistant.phone_assistant.ClaudeHandler"):
        with patch("src.assistant.phone_assistant.TwilioHandler"):
            from fastapi.testclient import TestClient
            from src.server import app

            # Set the mock assistant on app state
            app.state.assistant = mock_assistant

            yield TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "version" in data

    def test_health_endpoint(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data


class TestVoiceEndpoints:
    """Tests for voice call handling endpoints."""

    def test_incoming_call_success(self, client, mock_assistant):
        """Test successful incoming call handling."""
        response = client.post(
            "/voice/incoming",
            data={
                "From": "+14155559999",
                "To": "+14155551234",
                "CallSid": "CA12345"
            }
        )
        assert response.status_code == 200
        assert "xml" in response.headers.get("content-type", "")
        mock_assistant.handle_incoming_call.assert_called_once()

    def test_incoming_call_missing_from(self, client):
        """Test incoming call with missing From field."""
        response = client.post(
            "/voice/incoming",
            data={
                "To": "+14155551234"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_process_voice_success(self, client, mock_assistant):
        """Test successful voice processing."""
        response = client.post(
            "/voice/process",
            data={
                "From": "+14155559999",
                "SpeechResult": "Hello, I need help",
                "CallSid": "CA12345"
            }
        )
        assert response.status_code == 200
        assert "xml" in response.headers.get("content-type", "")
        mock_assistant.process_speech.assert_called_once()

    def test_process_voice_no_speech(self, client, mock_assistant):
        """Test voice processing with no speech result."""
        response = client.post(
            "/voice/process",
            data={
                "From": "+14155559999",
                "CallSid": "CA12345"
            }
        )
        assert response.status_code == 200
        # Should return "didn't catch" response
        mock_assistant.twilio.create_response_twiml.assert_called()

    def test_call_status_completed(self, client, mock_assistant):
        """Test call status callback for completed call."""
        response = client.post(
            "/voice/status",
            data={
                "CallSid": "CA12345",
                "CallStatus": "completed",
                "From": "+14155559999"
            }
        )
        assert response.status_code == 200
        mock_assistant.end_call.assert_called_once_with(caller_number="+14155559999")

    def test_call_status_in_progress(self, client, mock_assistant):
        """Test call status callback for in-progress call."""
        response = client.post(
            "/voice/status",
            data={
                "CallSid": "CA12345",
                "CallStatus": "in-progress"
            }
        )
        assert response.status_code == 200
        # Should not call end_call for in-progress status
        mock_assistant.end_call.assert_not_called()


class TestSMSEndpoint:
    """Tests for SMS handling endpoint."""

    def test_incoming_sms_success(self, client, mock_assistant):
        """Test successful SMS handling."""
        response = client.post(
            "/sms/incoming",
            data={
                "From": "+14155559999",
                "Body": "Hello, what's my appointment status?",
                "MessageSid": "SM12345"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        mock_assistant.claude.generate_response.assert_called_once()
        mock_assistant.send_sms_notification.assert_called_once()

    def test_incoming_sms_missing_body(self, client):
        """Test SMS with missing body."""
        response = client.post(
            "/sms/incoming",
            data={
                "From": "+14155559999"
            }
        )
        assert response.status_code == 422  # Validation error


class TestErrorHandling:
    """Tests for error handling."""

    def test_incoming_call_error(self, client, mock_assistant):
        """Test error handling in incoming call."""
        mock_assistant.handle_incoming_call.side_effect = Exception("Test error")

        response = client.post(
            "/voice/incoming",
            data={
                "From": "+14155559999",
                "CallSid": "CA12345"
            }
        )
        assert response.status_code == 200
        # Should return error TwiML
        assert "technical difficulties" in response.text.lower()

    def test_sms_error_no_internal_details(self, client, mock_assistant):
        """Test that SMS errors don't expose internal details."""
        mock_assistant.claude.generate_response.side_effect = Exception("Internal error details")

        response = client.post(
            "/sms/incoming",
            data={
                "From": "+14155559999",
                "Body": "Hello"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        # Should not expose internal error message
        assert "Internal error" not in data.get("message", "")
