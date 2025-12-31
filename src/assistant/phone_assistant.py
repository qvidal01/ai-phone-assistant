"""Main PhoneAssistant class that orchestrates all components."""

from typing import Optional, Dict
from src.assistant.claude_handler import ClaudeHandler
from src.assistant.ollama_handler import OllamaHandler
from src.assistant.gateway_handler import GatewayHandler
from src.assistant.ai_router import AIRouter, BackendType
from src.voice.twilio_handler import TwilioHandler
from src.integrations.crm_base import CRMBase
from src.integrations.mock_crm import MockCRM
from src.utils.config import Config, load_config
from src.utils.logger import setup_logger

# Import AIQSO-specific prompts
try:
    from src.prompts.aiqso_prompts import (
        VOICE_SYSTEM_PROMPT,
        GREETINGS,
        get_contextual_prompt,
        detect_intent,
    )
    AIQSO_PROMPTS_AVAILABLE = True
except ImportError:
    AIQSO_PROMPTS_AVAILABLE = False

# Import Odoo CRM if available
try:
    from src.integrations.odoo_crm import OdooCRM
    ODOO_AVAILABLE = True
except ImportError:
    ODOO_AVAILABLE = False

# Import EasyAppointments if available
try:
    from src.integrations.easyappointments import EasyAppointmentsClient
    EASYAPPOINTMENTS_AVAILABLE = True
except ImportError:
    EASYAPPOINTMENTS_AVAILABLE = False

# Import Action Handler
try:
    from src.assistant.action_handler import ActionHandler, ActionType, ConversationState
    ACTION_HANDLER_AVAILABLE = True
except ImportError:
    ACTION_HANDLER_AVAILABLE = False


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

        # Initialize Claude handler (cloud API)
        self.claude = ClaudeHandler(
            api_key=self.config.anthropic_api_key
        ) if self.config.anthropic_api_key else None

        # Initialize Ollama handler (local AI server)
        ollama_url = getattr(self.config, 'ollama_url', 'http://192.168.0.234:11434')
        ollama_model = getattr(self.config, 'ollama_default_model', 'quick-responder:latest')
        ai_timeout = getattr(self.config, 'ai_timeout', 15.0)  # Reduced timeout for voice
        self.ollama = OllamaHandler(
            base_url=ollama_url,
            default_model=ollama_model,
            timeout=ai_timeout
        )

        # Initialize AI Gateway handler (edge inference)
        gateway_url = getattr(self.config, 'ai_gateway_url', 'https://ai-gateway.aiqso.io')
        gateway_enabled = getattr(self.config, 'ai_gateway_enabled', True)
        self.gateway = None
        if gateway_enabled:
            try:
                self.gateway = GatewayHandler(base_url=gateway_url)
                self.logger.info(f"AI Gateway initialized: {gateway_url}")
            except Exception as e:
                self.logger.warning(f"AI Gateway initialization failed: {e}")

        # Initialize smart AI router with all backends
        prefer_local = getattr(self.config, 'prefer_local_ai', True)
        prefer_edge = getattr(self.config, 'prefer_edge_ai', False)
        self.ai_router = AIRouter(
            claude_handler=self.claude,
            ollama_handler=self.ollama,
            gateway_handler=self.gateway,
            default_strategy="hybrid",
            prefer_local=prefer_local,
            prefer_edge=prefer_edge
        )

        # Initialize Twilio handler with configured voice
        tts_voice = getattr(self.config, 'tts_voice', 'female_us')
        self.twilio = TwilioHandler(
            account_sid=self.config.twilio_account_sid,
            auth_token=self.config.twilio_auth_token,
            phone_number=self.config.twilio_phone_number,
            voice=tts_voice
        )
        self.logger.info(f"TTS Voice: {tts_voice}")

        # Initialize CRM (prefer Odoo if configured)
        if crm:
            self.crm = crm
        elif ODOO_AVAILABLE and getattr(self.config, 'odoo_url', None):
            try:
                self.crm = OdooCRM(
                    url=self.config.odoo_url,
                    database=self.config.odoo_database,
                    username=self.config.odoo_username,
                    password=self.config.odoo_password
                )
                self.logger.info("Odoo CRM initialized")
            except Exception as e:
                self.logger.warning(f"Odoo CRM initialization failed: {e}")
                self.crm = MockCRM()
        else:
            self.crm = MockCRM()

        # Initialize EasyAppointments for calendar booking
        self.appointments = None
        if EASYAPPOINTMENTS_AVAILABLE and getattr(self.config, 'easyappointments_token', None):
            try:
                self.appointments = EasyAppointmentsClient(
                    base_url=getattr(self.config, 'easyappointments_url', 'https://cal.aiqso.io'),
                    api_token=self.config.easyappointments_token
                )
                self.logger.info("EasyAppointments initialized")
            except Exception as e:
                self.logger.warning(f"EasyAppointments initialization failed: {e}")

        # Escalation phone number
        self.escalation_phone = getattr(self.config, 'escalation_phone', None)

        # Initialize Action Handler for booking and other actions
        self.action_handler = None
        if ACTION_HANDLER_AVAILABLE:
            self.action_handler = ActionHandler(
                appointments_client=self.appointments,
                crm_client=self.crm if not isinstance(self.crm, MockCRM) else None
            )
            self.logger.info("Action Handler initialized")

        # Track active calls with routing stats
        self.active_calls: Dict[str, Dict] = {}

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
                # Use AIQSO greeting for returning customers
                if AIQSO_PROMPTS_AVAILABLE:
                    greeting = GREETINGS.get("returning",
                        f"Welcome back! Great to hear from you, {customer.get('name', 'there')}. How can I help you today?")
                else:
                    greeting = (
                        f"Hello {customer.get('name', 'there')}! "
                        "Thank you for calling. How can I help you today?"
                    )
                self.logger.info(f"Recognized customer: {customer.get('name')}")
            else:
                # Use AIQSO standard greeting
                if AIQSO_PROMPTS_AVAILABLE:
                    greeting = GREETINGS.get("standard",
                        "Hello! Thank you for calling AIQSO. I'm your AI assistant. How can I help you today?")
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
        self,
        caller_number: str,
        speech_text: str,
        call_context: Optional[Dict] = None
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
            caller_name = ""
            if caller_number in self.active_calls:
                customer = self.active_calls[caller_number].get("customer")
                self.active_calls[caller_number]["query_count"] += 1
                if customer:
                    caller_name = customer.get("name", "")

            # Check for actionable intents FIRST (appointments, transfers, etc.)
            ai_response = None
            action_handled = False

            if self.action_handler:
                action_type, state = self.action_handler.detect_intent(speech_text, caller_number)

                if action_type == ActionType.BOOK_APPOINTMENT:
                    # Handle appointment booking flow
                    result = self.action_handler.process_booking_flow(
                        text=speech_text,
                        phone=caller_number,
                        caller_name=caller_name
                    )
                    ai_response = result.message
                    action_handled = True
                    self.logger.info(f"Action: {action_type.value}, State: {result.next_state.value}")

                elif action_type == ActionType.CHECK_AVAILABILITY:
                    result = self.action_handler.handle_availability_check()
                    ai_response = result.message
                    action_handled = True
                    self.logger.info(f"Action: {action_type.value}")

                elif action_type == ActionType.TRANSFER_TO_HUMAN:
                    result = self.action_handler.handle_transfer(caller_number, speech_text)
                    ai_response = result.message
                    action_handled = True
                    self.logger.info(f"Action: {action_type.value}")

                elif action_type == ActionType.LOG_CALLBACK:
                    result = self.action_handler.handle_callback(caller_number, speech_text)
                    ai_response = result.message
                    action_handled = True
                    self.logger.info(f"Action: {action_type.value}")

            # If no action was handled, use AI router for general response
            if not action_handled:
                # Build context for AI
                system_prompt = self._build_system_prompt(customer)

                # Use smart router to generate response
                ai_response, decision = self.ai_router.generate_response(
                    query=speech_text,
                    system_prompt=system_prompt,
                    context={"customer": customer, "caller": caller_number}
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
            if customer and not isinstance(self.crm, MockCRM):
                try:
                    self.crm.create_note(
                        customer_id=customer["id"],
                        note=f"User: {speech_text} | Assistant: {ai_response}"
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
            call_info = self.active_calls[caller_number]

            # Get conversation summary
            summary = self.ai_router.get_conversation_summary()

            # Log call statistics
            backends_used = call_info.get("backend_used", [])
            query_count = call_info.get("query_count", 0)
            self.logger.info(
                f"Call ended - Queries: {query_count}, "
                f"Backends used: {set(backends_used)}"
            )

            # Log summary to CRM if customer exists
            customer = call_info.get("customer")
            if customer:
                try:
                    self.crm.create_note(
                        customer_id=customer["id"],
                        note=f"Call Summary ({query_count} queries): {summary}"
                    )
                except Exception as e:
                    self.logger.error(f"Error logging call summary: {e}")

            # Reset conversations
            self.ai_router.reset_conversations()

            # Remove from active calls
            del self.active_calls[caller_number]

            self.logger.info(f"Call ended for: {caller_number}")

    def _build_system_prompt(self, customer: Optional[Dict] = None) -> str:
        """
        Build system prompt for AI with customer context.

        Args:
            customer: Optional customer data

        Returns:
            str: System prompt
        """
        # Use AIQSO-specific prompts if available
        if AIQSO_PROMPTS_AVAILABLE:
            caller_info = None
            if customer:
                caller_info = {
                    "name": customer.get('name', 'Unknown'),
                    "is_customer": True,
                    "notes": customer.get('notes', ''),
                }
            return get_contextual_prompt(caller_info=caller_info)

        # Fallback to generic prompt
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
            if customer.get('email'):
                customer_context += f"\nEmail: {customer['email']}"
            if customer.get('phone'):
                customer_context += f"\nPhone: {customer['phone']}"
            if customer.get('notes'):
                customer_context += f"\nNotes: {customer['notes']}"
            base_prompt += customer_context

        return base_prompt

    def get_stats(self) -> Dict:
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
        stats_with_percentages["ollama_percentage"] = round(
            (self.stats["ollama_fast"] + self.stats["ollama_chat"] + self.stats["ollama_smart"]) / total * 100, 1
        ) if total > 0 else 0
        stats_with_percentages["claude_percentage"] = round(
            self.stats["claude"] / total * 100, 1
        ) if total > 0 else 0

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
        print(f"\nAI Backends:")
        print(f"  - Ollama (local): {'✓ Online' if availability.get('ollama') else '✗ Offline'}")
        print(f"  - Claude (cloud): {'✓ Configured' if availability.get('claude') else '✗ Not configured'}")
        print(f"\nRouting Strategy: Smart (prefer local: {self.ai_router.prefer_local})")
        print(f"\nWaiting for incoming calls...")
        print(f"{'=' * 60}\n")
