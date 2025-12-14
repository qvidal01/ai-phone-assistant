"""Twilio voice integration for phone assistant."""

from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from src.utils.config import mask_phone_number
from src.utils.logger import setup_logger


class TwilioHandler:
    """Handles Twilio voice call operations."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        phone_number: str,
        speech_timeout: str = "auto",
        voice_language: str = "en-US",
        log_level: str = "INFO"
    ):
        """
        Initialize Twilio handler.

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            phone_number: Twilio phone number
            speech_timeout: Speech timeout setting (default: auto)
            voice_language: Voice recognition language (default: en-US)
            log_level: Logging level
        """
        self.client = Client(account_sid, auth_token)
        self.phone_number = phone_number
        self.speech_timeout = speech_timeout
        self.voice_language = voice_language
        self.logger = setup_logger(__name__, level=log_level)

    def create_greeting_response(self, greeting: Optional[str] = None) -> str:
        """
        Create TwiML response for greeting callers.

        Args:
            greeting: Custom greeting message

        Returns:
            str: TwiML XML response
        """
        response = VoiceResponse()

        if greeting is None:
            greeting = (
                "Hello! Thank you for calling. "
                "I'm your AI assistant. How can I help you today?"
            )

        # Use Gather to collect speech input
        gather = Gather(
            input='speech',
            action='/voice/process',
            method='POST',
            speech_timeout=self.speech_timeout,
            language=self.voice_language
        )
        gather.say(greeting)
        response.append(gather)

        # If no input received
        response.say("I didn't receive any input. Goodbye!")
        response.hangup()

        return str(response)

    def create_response_twiml(
        self,
        message: str,
        continue_conversation: bool = True
    ) -> str:
        """
        Create TwiML response with a message.

        Args:
            message: Message to speak to caller
            continue_conversation: Whether to continue listening

        Returns:
            str: TwiML XML response
        """
        response = VoiceResponse()

        if continue_conversation:
            # Gather more input after speaking
            gather = Gather(
                input='speech',
                action='/voice/process',
                method='POST',
                speech_timeout=self.speech_timeout,
                language=self.voice_language
            )
            gather.say(message)
            response.append(gather)

            # Fallback if no response
            response.say("Are you still there? Please say something or I'll end the call.")
            response.redirect('/voice/process', method='POST')
        else:
            # End conversation
            response.say(message)
            response.say("Thank you for calling. Goodbye!")
            response.hangup()

        return str(response)

    def make_call(
        self,
        to_number: str,
        message: str,
        callback_url: Optional[str] = None
    ) -> str:
        """
        Make an outbound call.

        Args:
            to_number: Phone number to call
            message: Message to speak
            callback_url: Optional callback URL for call status

        Returns:
            str: Call SID
        """
        try:
            response = VoiceResponse()
            response.say(message)

            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                twiml=str(response),
                status_callback=callback_url
            )

            # Log with masked phone number
            self.logger.info(f"Call initiated to {mask_phone_number(to_number)}: {call.sid}")
            return call.sid

        except Exception as e:
            self.logger.error(f"Error making call: {e}")
            raise

    def send_sms(self, to_number: str, message: str) -> str:
        """
        Send an SMS message.

        Args:
            to_number: Phone number to send to
            message: SMS message content

        Returns:
            str: Message SID
        """
        try:
            message_obj = self.client.messages.create(
                to=to_number,
                from_=self.phone_number,
                body=message
            )

            # Log with masked phone number
            self.logger.info(f"SMS sent to {mask_phone_number(to_number)}: {message_obj.sid}")
            return message_obj.sid

        except Exception as e:
            self.logger.error(f"Error sending SMS: {e}")
            raise

    def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """
        Get the status of a call.

        Args:
            call_sid: Call SID to check

        Returns:
            dict: Call status information
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "from": call.from_,
                "to": call.to
            }
        except Exception as e:
            self.logger.error(f"Error fetching call status: {e}")
            raise
