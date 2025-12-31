"""Action handler for executing real actions based on conversation context."""

import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from src.utils.logger import setup_logger


class ActionType(Enum):
    """Types of actions the assistant can take."""
    NONE = "none"
    BOOK_APPOINTMENT = "book_appointment"
    CHECK_AVAILABILITY = "check_availability"
    CANCEL_APPOINTMENT = "cancel_appointment"
    TRANSFER_TO_HUMAN = "transfer_to_human"
    SEND_INFO = "send_info"
    LOG_CALLBACK = "log_callback"


class ConversationState(Enum):
    """States for multi-turn conversations."""
    IDLE = "idle"
    COLLECTING_EMAIL = "collecting_email"
    COLLECTING_TIME = "collecting_time"
    COLLECTING_NAME = "collecting_name"
    CONFIRMING_BOOKING = "confirming_booking"
    AWAITING_CONFIRMATION = "awaiting_confirmation"


@dataclass
class BookingContext:
    """Context for appointment booking flow."""
    state: ConversationState = ConversationState.IDLE
    caller_phone: str = ""
    caller_name: str = ""
    caller_email: str = ""
    preferred_date: str = ""
    preferred_time: str = ""
    service_type: str = "consultation"
    notes: str = ""
    attempts: int = 0


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    message: str
    action_type: ActionType
    data: Dict = field(default_factory=dict)
    next_state: ConversationState = ConversationState.IDLE


class ActionHandler:
    """
    Handles action detection and execution for the phone assistant.

    This class manages multi-turn conversations for complex actions like
    appointment booking, which require collecting multiple pieces of information.
    """

    def __init__(self, appointments_client=None, crm_client=None):
        """
        Initialize action handler.

        Args:
            appointments_client: EasyAppointments client
            crm_client: CRM client (Odoo)
        """
        self.appointments = appointments_client
        self.crm = crm_client
        self.logger = setup_logger(__name__)

        # Active booking contexts by phone number
        self.booking_contexts: Dict[str, BookingContext] = {}

        # Email regex pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )

        # Time patterns
        self.time_patterns = [
            r'(\d{1,2})\s*(?::|\.)\s*(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?',
            r'(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)',
            r'(morning|afternoon|evening)',
            r'(noon|midnight)',
        ]

        # Date patterns
        self.date_keywords = {
            'today': 0, 'tomorrow': 1,
            'monday': None, 'tuesday': None, 'wednesday': None,
            'thursday': None, 'friday': None, 'saturday': None, 'sunday': None,
            'next week': 7, 'this week': 0,
        }

        # Appointment intent patterns
        self.appointment_patterns = [
            r'(schedule|book|set up|make|arrange)\s*(an?)?\s*(appointment|meeting|call|consultation|demo)',
            r'(want|like|need)\s*to\s*(schedule|book|meet|talk|speak)',
            r'(available|availability|free|open)\s*(times?|slots?|appointments?)?',
            r'(can i|could i|may i)\s*(schedule|book|come in|meet)',
        ]

        # Confirmation patterns
        self.yes_patterns = [r'\b(yes|yeah|yep|sure|ok|okay|correct|right|confirm|perfect|great|sounds good)\b']
        self.no_patterns = [r'\b(no|nope|nah|cancel|wrong|incorrect|change|different)\b']

    def get_or_create_context(self, phone: str) -> BookingContext:
        """Get or create a booking context for a caller."""
        if phone not in self.booking_contexts:
            self.booking_contexts[phone] = BookingContext(caller_phone=phone)
        return self.booking_contexts[phone]

    def clear_context(self, phone: str):
        """Clear booking context for a caller."""
        if phone in self.booking_contexts:
            del self.booking_contexts[phone]

    def detect_intent(self, text: str, phone: str) -> Tuple[ActionType, ConversationState]:
        """
        Detect the intent from user's speech.

        Args:
            text: User's speech text
            phone: Caller's phone number

        Returns:
            Tuple of (ActionType, current ConversationState)
        """
        text_lower = text.lower().strip()
        context = self.get_or_create_context(phone)

        # If we're in a booking flow, continue it
        if context.state != ConversationState.IDLE:
            return ActionType.BOOK_APPOINTMENT, context.state

        # Check for appointment intent
        for pattern in self.appointment_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return ActionType.BOOK_APPOINTMENT, ConversationState.IDLE

        # Check for availability check
        if re.search(r'(when|what)\s*(are|is)\s*(you|your|the)?\s*(available|open|free)', text_lower):
            return ActionType.CHECK_AVAILABILITY, ConversationState.IDLE

        # Check for transfer to human
        if re.search(r'(speak|talk)\s*(to|with)?\s*(a|an)?\s*(person|human|agent|someone|representative)', text_lower):
            return ActionType.TRANSFER_TO_HUMAN, ConversationState.IDLE

        # Check for callback request
        if re.search(r'(call|callback|call back|ring)\s*(me)?\s*(back)?', text_lower):
            return ActionType.LOG_CALLBACK, ConversationState.IDLE

        return ActionType.NONE, ConversationState.IDLE

    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        # Handle spoken email formats
        text = text.lower()
        text = text.replace(' at ', '@').replace(' dot ', '.')
        text = text.replace(' underscore ', '_').replace(' dash ', '-')
        text = re.sub(r'\s+', '', text)  # Remove spaces

        match = self.email_pattern.search(text)
        if match:
            return match.group(0)
        return None

    def extract_date(self, text: str) -> Optional[str]:
        """Extract date from text, return as YYYY-MM-DD."""
        text_lower = text.lower()
        today = datetime.now()

        # Check for relative dates
        for keyword, days_offset in self.date_keywords.items():
            if keyword in text_lower:
                if days_offset is not None:
                    target_date = today + timedelta(days=days_offset)
                    return target_date.strftime("%Y-%m-%d")
                else:
                    # It's a day name, find next occurrence
                    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    if keyword in day_names:
                        target_day = day_names.index(keyword)
                        current_day = today.weekday()
                        days_ahead = target_day - current_day
                        if days_ahead <= 0:
                            days_ahead += 7
                        target_date = today + timedelta(days=days_ahead)
                        return target_date.strftime("%Y-%m-%d")

        return None

    def extract_time(self, text: str) -> Optional[str]:
        """Extract time from text, return as HH:MM."""
        text_lower = text.lower()

        # Handle word times
        if 'noon' in text_lower:
            return "12:00"
        if 'morning' in text_lower:
            return "09:00"
        if 'afternoon' in text_lower:
            return "14:00"
        if 'evening' in text_lower:
            return "17:00"

        # Try numeric patterns
        match = re.search(r'(\d{1,2})\s*(?::|\.)?(\d{2})?\s*(am|pm|a\.m\.|p\.m\.)?', text_lower, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3)

            if period and 'p' in period.lower() and hour < 12:
                hour += 12
            elif period and 'a' in period.lower() and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute:02d}"

        return None

    def is_confirmation(self, text: str) -> Optional[bool]:
        """Check if text is a yes/no confirmation."""
        text_lower = text.lower()

        for pattern in self.yes_patterns:
            if re.search(pattern, text_lower):
                return True

        for pattern in self.no_patterns:
            if re.search(pattern, text_lower):
                return False

        return None

    def process_booking_flow(
        self,
        text: str,
        phone: str,
        caller_name: str = ""
    ) -> ActionResult:
        """
        Process a step in the appointment booking flow.

        Args:
            text: User's speech text
            phone: Caller's phone number
            caller_name: Caller's name if known

        Returns:
            ActionResult with response message and next state
        """
        context = self.get_or_create_context(phone)
        context.attempts += 1

        if caller_name and not context.caller_name:
            context.caller_name = caller_name

        # State machine for booking flow
        if context.state == ConversationState.IDLE:
            # Starting a new booking - ask for email
            context.state = ConversationState.COLLECTING_EMAIL
            return ActionResult(
                success=True,
                message="I'd be happy to schedule a consultation for you! What email address should I send the calendar invite to?",
                action_type=ActionType.BOOK_APPOINTMENT,
                next_state=ConversationState.COLLECTING_EMAIL
            )

        elif context.state == ConversationState.COLLECTING_EMAIL:
            email = self.extract_email(text)
            if email:
                context.caller_email = email
                context.state = ConversationState.COLLECTING_TIME
                return ActionResult(
                    success=True,
                    message=f"Great, I'll send the invite to {email}. When would you like to meet? I have availability this week.",
                    action_type=ActionType.BOOK_APPOINTMENT,
                    next_state=ConversationState.COLLECTING_TIME
                )
            else:
                if context.attempts > 3:
                    self.clear_context(phone)
                    return ActionResult(
                        success=False,
                        message="I'm having trouble getting your email. Would you like me to have someone call you back instead?",
                        action_type=ActionType.BOOK_APPOINTMENT,
                        next_state=ConversationState.IDLE
                    )
                return ActionResult(
                    success=True,
                    message="I didn't catch that email. Could you spell it out for me? For example, john at gmail dot com.",
                    action_type=ActionType.BOOK_APPOINTMENT,
                    next_state=ConversationState.COLLECTING_EMAIL
                )

        elif context.state == ConversationState.COLLECTING_TIME:
            date = self.extract_date(text)
            time = self.extract_time(text)

            if date:
                context.preferred_date = date
            if time:
                context.preferred_time = time

            if context.preferred_date or context.preferred_time:
                context.state = ConversationState.CONFIRMING_BOOKING

                # Format the confirmation
                date_str = context.preferred_date or "this week"
                time_str = context.preferred_time or "a convenient time"

                if context.preferred_date:
                    try:
                        dt = datetime.strptime(context.preferred_date, "%Y-%m-%d")
                        date_str = dt.strftime("%A, %B %d")
                    except:
                        pass

                if context.preferred_time:
                    try:
                        dt = datetime.strptime(context.preferred_time, "%H:%M")
                        time_str = dt.strftime("%I:%M %p").lstrip("0")
                    except:
                        pass

                return ActionResult(
                    success=True,
                    message=f"Let me confirm: A consultation on {date_str} at {time_str}, with the invite going to {context.caller_email}. Does that sound right?",
                    action_type=ActionType.BOOK_APPOINTMENT,
                    next_state=ConversationState.CONFIRMING_BOOKING
                )
            else:
                # Try to get availability from calendar
                if self.appointments:
                    try:
                        slots = self.appointments.get_next_available_slots(days_ahead=5)
                        if slots:
                            slot = slots[0]
                            times = ", ".join(slot["times"][:3])
                            return ActionResult(
                                success=True,
                                message=f"I have openings on {slot['day']} at {times}. Which works for you?",
                                action_type=ActionType.BOOK_APPOINTMENT,
                                next_state=ConversationState.COLLECTING_TIME
                            )
                    except Exception as e:
                        self.logger.error(f"Error getting availability: {e}")

                return ActionResult(
                    success=True,
                    message="What day and time works best for you? We're available Monday through Friday.",
                    action_type=ActionType.BOOK_APPOINTMENT,
                    next_state=ConversationState.COLLECTING_TIME
                )

        elif context.state == ConversationState.CONFIRMING_BOOKING:
            confirmation = self.is_confirmation(text)

            if confirmation is True:
                # Actually book the appointment!
                result = self._execute_booking(context)
                self.clear_context(phone)
                return result

            elif confirmation is False:
                context.state = ConversationState.COLLECTING_EMAIL
                context.caller_email = ""
                context.preferred_date = ""
                context.preferred_time = ""
                return ActionResult(
                    success=True,
                    message="No problem, let's start over. What email should I use for the invite?",
                    action_type=ActionType.BOOK_APPOINTMENT,
                    next_state=ConversationState.COLLECTING_EMAIL
                )
            else:
                return ActionResult(
                    success=True,
                    message="Just to confirm - should I book this appointment? Say yes to confirm or no to change something.",
                    action_type=ActionType.BOOK_APPOINTMENT,
                    next_state=ConversationState.CONFIRMING_BOOKING
                )

        # Fallback
        return ActionResult(
            success=False,
            message="I'm sorry, I got a bit confused. Would you like to schedule an appointment?",
            action_type=ActionType.NONE,
            next_state=ConversationState.IDLE
        )

    def _execute_booking(self, context: BookingContext) -> ActionResult:
        """Actually execute the booking through EasyAppointments."""
        if not self.appointments:
            return ActionResult(
                success=False,
                message="I apologize, but I'm unable to book appointments right now. Please call back during business hours or visit aiqso.io to schedule online.",
                action_type=ActionType.BOOK_APPOINTMENT,
                data={"error": "appointments_client_not_configured"}
            )

        try:
            # Use default date/time if not specified
            if not context.preferred_date:
                # Default to tomorrow
                context.preferred_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            if not context.preferred_time:
                # Default to 10 AM
                context.preferred_time = "10:00"

            # Extract name from email if not provided
            if not context.caller_name:
                email_name = context.caller_email.split('@')[0]
                context.caller_name = email_name.replace('.', ' ').replace('_', ' ').title()

            # Book through EasyAppointments
            result = self.appointments.book_appointment(
                phone=context.caller_phone,
                name=context.caller_name,
                email=context.caller_email,
                preferred_date=context.preferred_date,
                preferred_time=context.preferred_time,
                notes=f"Booked via AI Phone Assistant"
            )

            if result.get("success"):
                # Format nice confirmation
                try:
                    dt = datetime.strptime(f"{result['date']} {result['time']}", "%Y-%m-%d %H:%M")
                    formatted = dt.strftime("%A, %B %d at %I:%M %p").replace(" 0", " ")
                except:
                    formatted = f"{result.get('date', 'soon')} at {result.get('time', 'your requested time')}"

                return ActionResult(
                    success=True,
                    message=f"You're all set! I've booked your consultation for {formatted}. A calendar invite is on its way to {context.caller_email}. Is there anything else I can help with?",
                    action_type=ActionType.BOOK_APPOINTMENT,
                    data=result
                )
            else:
                # Booking failed but we have a suggestion
                if "suggestion" in result:
                    return ActionResult(
                        success=False,
                        message=f"That time isn't available. {result['suggestion']} Would that work?",
                        action_type=ActionType.BOOK_APPOINTMENT,
                        next_state=ConversationState.COLLECTING_TIME,
                        data=result
                    )
                return ActionResult(
                    success=False,
                    message="I wasn't able to book that time. Would you like to try a different day?",
                    action_type=ActionType.BOOK_APPOINTMENT,
                    next_state=ConversationState.COLLECTING_TIME
                )

        except Exception as e:
            self.logger.error(f"Error booking appointment: {e}")
            return ActionResult(
                success=False,
                message="I ran into a problem booking that. Let me have someone call you back to confirm your appointment.",
                action_type=ActionType.BOOK_APPOINTMENT,
                data={"error": str(e)}
            )

    def handle_transfer(self, phone: str, reason: str = "") -> ActionResult:
        """Handle transfer to human request."""
        return ActionResult(
            success=True,
            message="I understand you'd like to speak with someone directly. I'll have a team member call you back within the hour. Is that okay?",
            action_type=ActionType.TRANSFER_TO_HUMAN,
            data={"phone": phone, "reason": reason}
        )

    def handle_callback(self, phone: str, reason: str = "") -> ActionResult:
        """Handle callback request."""
        if self.crm:
            try:
                self.crm.log_call(
                    phone_number=phone,
                    summary=f"Callback requested: {reason}" if reason else "Callback requested via AI assistant"
                )
            except Exception as e:
                self.logger.error(f"Error logging callback: {e}")

        return ActionResult(
            success=True,
            message="I've noted your callback request. Someone from our team will call you back shortly. Is there anything specific you'd like them to know?",
            action_type=ActionType.LOG_CALLBACK,
            data={"phone": phone, "reason": reason}
        )

    def handle_availability_check(self) -> ActionResult:
        """Handle availability check request."""
        if self.appointments:
            try:
                slots = self.appointments.get_next_available_slots(days_ahead=5)
                if slots:
                    # Format nicely
                    availability = []
                    for slot in slots[:3]:
                        times = " and ".join(slot["times"][:2])
                        availability.append(f"{slot['day']} at {times}")

                    msg = f"We have availability on {', '.join(availability)}. Would you like to book one of those times?"
                    return ActionResult(
                        success=True,
                        message=msg,
                        action_type=ActionType.CHECK_AVAILABILITY,
                        data={"slots": slots}
                    )
            except Exception as e:
                self.logger.error(f"Error checking availability: {e}")

        return ActionResult(
            success=True,
            message="We're generally available Monday through Friday, 9 AM to 6 PM Central. Would you like to schedule a specific time?",
            action_type=ActionType.CHECK_AVAILABILITY
        )
