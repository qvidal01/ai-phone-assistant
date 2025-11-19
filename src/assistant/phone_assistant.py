"""Main PhoneAssistant class that orchestrates all components."""

from typing import Optional, Dict
from src.assistant.claude_handler import ClaudeHandler
from src.voice.twilio_handler import TwilioHandler
from src.integrations.crm_base import CRMBase
from src.integrations.mock_crm import MockCRM
from src.utils.config import Config, load_config
from src.utils.logger import setup_logger


class PhoneAssistant:
    """
    Main AI Phone Assistant class.

    This class orchestrates the Claude AI handler, Twilio voice integration,
    and CRM integration to provide an intelligent phone assistant service.
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        crm: Optional[CRMBase] = None
    ):
        """
        Initialize the Phone Assistant.

        Args:
            config: Optional configuration object. If not provided, loads from environment.
            crm: Optional CRM integration. If not provided, uses MockCRM.
        """
        # Load configuration
        self.config = config or load_config()
        self.logger = setup_logger(__name__, level=self.config.log_level)

        # Initialize components
        self.claude = ClaudeHandler(
            api_key=self.config.anthropic_api_key
        )

        self.twilio = TwilioHandler(
            account_sid=self.config.twilio_account_sid,
            auth_token=self.config.twilio_auth_token,
            phone_number=self.config.twilio_phone_number
        )

        self.crm = crm or MockCRM()

        # Track active calls
        self.active_calls: Dict[str, Dict] = {}

        self.logger.info("Phone Assistant initialized successfully")

    def handle_incoming_call(self, caller_number: str) -> str:
        """
        Handle an incoming call.

        Args:
            caller_number: Caller's phone number

        Returns:
            str: TwiML response for greeting
        """
        try:
            # Look up customer in CRM
            customer = self.crm.get_customer(caller_number)

            if customer:
                greeting = (
                    f"Hello {customer.get('name', 'there')}! "
                    "Thank you for calling. How can I help you today?"
                )
                self.logger.info(f"Recognized customer: {customer.get('name')}")
            else:
                greeting = (
                    "Hello! Thank you for calling. "
                    "I'm your AI assistant. How can I help you today?"
                )
                self.logger.info(f"New caller: {caller_number}")

            # Initialize conversation for this caller
            self.active_calls[caller_number] = {
                "customer": customer,
                "call_start": None
            }

            return self.twilio.create_greeting_response(greeting)

        except Exception as e:
            self.logger.error(f"Error handling incoming call: {e}")
            return self.twilio.create_greeting_response()

    def process_speech(
        self,
        caller_number: str,
        speech_text: str,
        call_context: Optional[Dict] = None
    ) -> str:
        """
        Process speech input from caller and generate response.

        Args:
            caller_number: Caller's phone number
            speech_text: Transcribed speech from caller
            call_context: Optional additional context

        Returns:
            str: TwiML response
        """
        try:
            # Get customer info if available
            customer = None
            if caller_number in self.active_calls:
                customer = self.active_calls[caller_number].get("customer")

            # Build context for Claude
            system_prompt = self._build_system_prompt(customer)

            # Generate AI response
            ai_response = self.claude.generate_response(
                user_message=speech_text,
                system_prompt=system_prompt
            )

            # Log the interaction to CRM if customer exists
            if customer:
                try:
                    self.crm.create_note(
                        customer_id=customer["id"],
                        note=f"Call interaction - User: {speech_text} | Assistant: {ai_response}"
                    )
                except Exception as e:
                    self.logger.error(f"Error logging to CRM: {e}")

            # Determine if conversation should continue
            continue_conversation = not any(
                phrase in ai_response.lower()
                for phrase in ["goodbye", "thank you for calling", "have a great day"]
            )

            return self.twilio.create_response_twiml(
                message=ai_response,
                continue_conversation=continue_conversation
            )

        except Exception as e:
            self.logger.error(f"Error processing speech: {e}")
            error_message = "I apologize, I'm having trouble processing that. Could you please try again?"
            return self.twilio.create_response_twiml(error_message, continue_conversation=True)

    def make_outbound_call(
        self,
        to_number: str,
        message: str,
        callback_url: Optional[str] = None
    ) -> str:
        """
        Make an outbound call.

        Args:
            to_number: Phone number to call
            message: Message to deliver
            callback_url: Optional callback URL

        Returns:
            str: Call SID
        """
        try:
            call_sid = self.twilio.make_call(
                to_number=to_number,
                message=message,
                callback_url=callback_url
            )
            self.logger.info(f"Outbound call initiated: {call_sid}")
            return call_sid
        except Exception as e:
            self.logger.error(f"Error making outbound call: {e}")
            raise

    def send_sms_notification(self, to_number: str, message: str) -> str:
        """
        Send an SMS notification.

        Args:
            to_number: Phone number to send to
            message: SMS message

        Returns:
            str: Message SID
        """
        try:
            message_sid = self.twilio.send_sms(
                to_number=to_number,
                message=message
            )
            self.logger.info(f"SMS notification sent: {message_sid}")
            return message_sid
        except Exception as e:
            self.logger.error(f"Error sending SMS: {e}")
            raise

    def end_call(self, caller_number: str) -> None:
        """
        Clean up after a call ends.

        Args:
            caller_number: Caller's phone number
        """
        if caller_number in self.active_calls:
            # Get conversation summary
            summary = self.claude.get_conversation_summary()

            # Log summary to CRM if customer exists
            customer = self.active_calls[caller_number].get("customer")
            if customer:
                try:
                    self.crm.create_note(
                        customer_id=customer["id"],
                        note=f"Call Summary: {summary}"
                    )
                except Exception as e:
                    self.logger.error(f"Error logging call summary: {e}")

            # Reset conversation
            self.claude.reset_conversation()

            # Remove from active calls
            del self.active_calls[caller_number]

            self.logger.info(f"Call ended for: {caller_number}")

    def _build_system_prompt(self, customer: Optional[Dict] = None) -> str:
        """
        Build system prompt for Claude with customer context.

        Args:
            customer: Optional customer data

        Returns:
            str: System prompt
        """
        base_prompt = (
            "You are a helpful phone assistant handling customer inquiries. "
            "You can help with appointment scheduling, status updates, and "
            "general questions. Be professional, friendly, and concise in "
            "your responses as this is a phone conversation. "
            "Keep responses brief and to the point."
        )

        if customer:
            customer_context = f"\n\nCurrent caller: {customer.get('name', 'Unknown')}"
            if customer.get('email'):
                customer_context += f"\nEmail: {customer['email']}"
            base_prompt += customer_context

        return base_prompt

    def start(self):
        """
        Start the phone assistant service.

        This is a placeholder for starting a web server to handle webhooks.
        In production, this would start a FastAPI/Flask server.
        """
        self.logger.info("Phone Assistant service started")
        self.logger.info(f"Ready to receive calls at: {self.config.twilio_phone_number}")
        print(f"📞 Phone Assistant is ready!")
        print(f"Phone Number: {self.config.twilio_phone_number}")
        print("Waiting for incoming calls...")
