"""Main PhoneAssistant class that orchestrates all components."""

from typing import Optional

from src.assistant.ai_router import AIRouter, BackendType
from src.assistant.claude_handler import ClaudeHandler
from src.assistant.ollama_handler import OllamaHandler
from src.integrations.crm_base import CRMBase
from src.integrations.mock_crm import MockCRM
from src.utils.config import Config, load_config
from src.utils.logger import setup_logger
from src.voice.twilio_handler import TwilioHandler


class PhoneAssistant:
    """
    Main AI Phone Assistant class.

    This class orchestrates the AI handlers (Claude + Ollama), Twilio voice integration,
    and CRM integration to provide an intelligent phone assistant service.

    Features:
    - Smart routing between Claude API and local Ollama models
    - Automatic fallback if primary backend fails
    - Cost optimization by preferring local models for simple queries
    - Full conversation context management
    """

    def __init__(self, config: Optional[Config] = None, crm: Optional[CRMBase] = None):
        """
        Initialize the Phone Assistant.

        Args:
            config: Optional configuration object. If not provided, loads from environment.
            crm: Optional CRM integration. If not provided, uses MockCRM.
        """
        # Load configuration
        self.config = config or load_config()
        self.logger = setup_logger(__name__, level=self.config.log_level)

        # Initialize Claude handler (cloud API)
        self.claude = (
            ClaudeHandler(api_key=self.config.anthropic_api_key)
            if self.config.anthropic_api_key
            else None
        )

        # Initialize Ollama handler (local AI server)
        ollama_url = getattr(self.config, "ollama_url", "http://192.168.0.234:11434")
        ollama_model = getattr(self.config, "ollama_default_model", "quick-responder:latest")
        self.ollama = OllamaHandler(base_url=ollama_url, default_model=ollama_model)

        # Initialize smart AI router
        prefer_local = getattr(self.config, "prefer_local_ai", True)
        self.ai_router = AIRouter(
            claude_handler=self.claude,
            ollama_handler=self.ollama,
            default_strategy="hybrid",
            prefer_local=prefer_local,
        )

        # Initialize Twilio handler
        self.twilio = TwilioHandler(
            account_sid=self.config.twilio_account_sid,
            auth_token=self.config.twilio_auth_token,
            phone_number=self.config.twilio_phone_number,
        )

        self.crm = crm or MockCRM()

        # Track active calls with routing stats
        self.active_calls: dict[str, dict] = {}

        # Stats tracking
        self.stats = {
            "total_queries": 0,
            "ollama_fast": 0,
            "ollama_chat": 0,
            "ollama_smart": 0,
            "claude": 0,
            "hybrid_fallback": 0,
        }

        self.logger.info("Phone Assistant initialized with multi-backend support")
        self._log_backend_status()

    def _log_backend_status(self):
        """Log the status of available backends."""
        availability = self.ai_router.check_backend_availability()
        self.logger.info(f"Backend availability: {availability}")

        if self.ollama:
            self.logger.info(f"Ollama URL: {self.ollama.base_url}")
            self.logger.info(f"Ollama default model: {self.ollama.default_model}")

        if self.claude:
            self.logger.info("Claude API configured")

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
                "call_start": None,
                "backend_used": [],
                "query_count": 0,
            }

            # Reset conversation history for new call
            self.ai_router.reset_conversations()

            return self.twilio.create_greeting_response(greeting)

        except Exception as e:
            self.logger.error(f"Error handling incoming call: {e}")
            return self.twilio.create_greeting_response()

    def process_speech(
        self, caller_number: str, speech_text: str, call_context: Optional[dict] = None
    ) -> str:
        """
        Process speech input from caller and generate response using smart routing.

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
                self.active_calls[caller_number]["query_count"] += 1

            # Build context for AI
            system_prompt = self._build_system_prompt(customer)

            # Use smart router to generate response
            ai_response, decision = self.ai_router.generate_response(
                query=speech_text,
                system_prompt=system_prompt,
                context={"customer": customer, "caller": caller_number},
            )

            # Track stats
            self.stats["total_queries"] += 1
            self._track_backend_usage(decision.backend)

            # Track backend used for this call
            if caller_number in self.active_calls:
                self.active_calls[caller_number]["backend_used"].append(decision.backend.value)

            self.logger.info(
                f"Query routed to {decision.backend.value} "
                f"(complexity: {decision.complexity.value}) - {decision.reason}"
            )

            # Log the interaction to CRM if customer exists
            if customer:
                try:
                    self.crm.create_note(
                        customer_id=customer["id"],
                        note=f"[{decision.backend.value}] User: {speech_text} | Assistant: {ai_response}",
                    )
                except Exception as e:
                    self.logger.error(f"Error logging to CRM: {e}")

            # Determine if conversation should continue
            continue_conversation = not any(
                phrase in ai_response.lower()
                for phrase in ["goodbye", "thank you for calling", "have a great day"]
            )

            return self.twilio.create_response_twiml(
                message=ai_response, continue_conversation=continue_conversation
            )

        except Exception as e:
            self.logger.error(f"Error processing speech: {e}")
            error_message = (
                "I apologize, I'm having trouble processing that. Could you please try again?"
            )
            return self.twilio.create_response_twiml(error_message, continue_conversation=True)

    def _track_backend_usage(self, backend: BackendType):
        """Track which backend was used."""
        if backend == BackendType.OLLAMA_FAST:
            self.stats["ollama_fast"] += 1
        elif backend == BackendType.OLLAMA_CHAT:
            self.stats["ollama_chat"] += 1
        elif backend == BackendType.OLLAMA_SMART:
            self.stats["ollama_smart"] += 1
        elif backend == BackendType.CLAUDE:
            self.stats["claude"] += 1
        elif backend == BackendType.HYBRID:
            self.stats["hybrid_fallback"] += 1

    def make_outbound_call(
        self, to_number: str, message: str, callback_url: Optional[str] = None
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
                to_number=to_number, message=message, callback_url=callback_url
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
            message_sid = self.twilio.send_sms(to_number=to_number, message=message)
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
            call_info = self.active_calls[caller_number]

            # Get conversation summary
            summary = self.ai_router.get_conversation_summary()

            # Log call statistics
            backends_used = call_info.get("backend_used", [])
            query_count = call_info.get("query_count", 0)
            self.logger.info(
                f"Call ended - Queries: {query_count}, " f"Backends used: {set(backends_used)}"
            )

            # Log summary to CRM if customer exists
            customer = call_info.get("customer")
            if customer:
                try:
                    self.crm.create_note(
                        customer_id=customer["id"],
                        note=f"Call Summary ({query_count} queries): {summary}",
                    )
                except Exception as e:
                    self.logger.error(f"Error logging call summary: {e}")

            # Reset conversations
            self.ai_router.reset_conversations()

            # Remove from active calls
            del self.active_calls[caller_number]

            self.logger.info(f"Call ended for: {caller_number}")

    def _build_system_prompt(self, customer: Optional[dict] = None) -> str:
        """
        Build system prompt for AI with customer context.

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
            "Keep responses brief - ideally 1-2 sentences. "
            "Avoid technical jargon and speak naturally."
        )

        if customer:
            customer_context = f"\n\nCurrent caller: {customer.get('name', 'Unknown')}"
            if customer.get("email"):
                customer_context += f"\nEmail: {customer['email']}"
            if customer.get("phone"):
                customer_context += f"\nPhone: {customer['phone']}"
            if customer.get("notes"):
                customer_context += f"\nNotes: {customer['notes']}"
            base_prompt += customer_context

        return base_prompt

    def get_stats(self) -> dict:
        """
        Get usage statistics.

        Returns:
            Dict: Usage statistics
        """
        total = self.stats["total_queries"]
        if total == 0:
            return self.stats

        # Calculate percentages
        stats_with_percentages = self.stats.copy()
        stats_with_percentages["ollama_percentage"] = (
            round(
                (self.stats["ollama_fast"] + self.stats["ollama_chat"] + self.stats["ollama_smart"])
                / total
                * 100,
                1,
            )
            if total > 0
            else 0
        )
        stats_with_percentages["claude_percentage"] = (
            round(self.stats["claude"] / total * 100, 1) if total > 0 else 0
        )

        return stats_with_percentages

    def start(self):
        """
        Start the phone assistant service.

        This is a placeholder for starting a web server to handle webhooks.
        In production, this would start a FastAPI/Flask server.
        """
        self.logger.info("Phone Assistant service started with multi-backend AI")
        self.logger.info(f"Ready to receive calls at: {self.config.twilio_phone_number}")

        # Check backend availability
        availability = self.ai_router.check_backend_availability()

        print(f"\n{'=' * 60}")
        print("AI Phone Assistant - Multi-Backend Edition")
        print(f"{'=' * 60}")
        print(f"\nPhone Number: {self.config.twilio_phone_number}")
        print("\nAI Backends:")
        print(f"  - Ollama (local): {'✓ Online' if availability.get('ollama') else '✗ Offline'}")
        print(
            f"  - Claude (cloud): {'✓ Configured' if availability.get('claude') else '✗ Not configured'}"
        )
        print(f"\nRouting Strategy: Smart (prefer local: {self.ai_router.prefer_local})")
        print("\nWaiting for incoming calls...")
        print(f"{'=' * 60}\n")
