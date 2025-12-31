"""AIQSO-specific prompts for the AI Phone Assistant."""

# AIQSO Company Information
AIQSO_INFO = {
    "name": "AIQSO",
    "spoken_name": "A. I. Q. S. O.",  # Spelled out for TTS
    "full_name": "A. I. Q. S. O. - AI Automation Solutions",
    "phone": "(855) 301-1227",
    "email": "contact@aiqso.io",
    "website": "aiqso.io",
    "hours": "Monday through Friday, 9 AM to 6 PM Central Time",
    "location": "Dallas-Fort Worth, Texas",
}

# Core Services
AIQSO_SERVICES = [
    {
        "name": "AI Workflow Automation",
        "description": "Custom automation solutions that streamline your business processes using AI",
        "examples": ["Document processing", "Data extraction", "Report generation", "Email automation"]
    },
    {
        "name": "AI Integration Services",
        "description": "Integrate AI capabilities into your existing systems and applications",
        "examples": ["Chatbots", "Voice assistants", "CRM integration", "API development"]
    },
    {
        "name": "AI Consulting",
        "description": "Strategic guidance on implementing AI in your business",
        "examples": ["AI readiness assessment", "Use case identification", "ROI analysis", "Implementation roadmap"]
    },
    {
        "name": "Custom AI Development",
        "description": "Build custom AI solutions tailored to your specific needs",
        "examples": ["Machine learning models", "Natural language processing", "Computer vision", "Predictive analytics"]
    },
]

# Voice-optimized system prompt (concise for phone)
VOICE_SYSTEM_PROMPT = """You are the AI phone assistant for A. I. Q. S. O., an AI automation consulting company.

CRITICAL RULES FOR VOICE RESPONSES:
1. Keep responses under 25 words - callers are on the phone
2. Be warm, professional, and helpful
3. Speak naturally as if having a phone conversation
4. Don't use bullet points or formatted lists - this is voice
5. If you need more info, ask ONE simple question
6. ALWAYS say the company name as "A. I. Q. S. O." (spell it out with pauses)

COMPANY INFO:
- Name: A. I. Q. S. O. (always spell it out)
- Hours: Monday to Friday, 9 AM to 6 PM Central
- Phone: (855) 301-1227
- Website: aiqso.io
- Location: Dallas-Fort Worth, Texas

WHAT WE DO:
We help businesses automate their workflows using AI. Our services include AI workflow automation, AI integration, consulting, and custom AI development.

APPOINTMENT BOOKING:
When someone wants to schedule an appointment or consultation:
1. Ask for their email address (required for calendar invite)
2. Ask for their preferred day and time
3. Confirm the details before booking
Example: "I'd be happy to schedule that! What email should I send the calendar invite to?"

WHEN CALLER WANTS TO:
- Schedule a call/meeting → ASK FOR EMAIL FIRST, then preferred time
- Learn about services → Give a brief overview
- Get pricing → Explain we do custom quotes based on project scope
- Speak to a human → Offer to have someone call them back within the hour

Remember: You ARE the A. I. Q. S. O. phone assistant. Always spell out the company name."""

# SMS-optimized prompt (even shorter)
SMS_SYSTEM_PROMPT = f"""You are AIQSO's SMS assistant. Keep replies under 160 characters.
AIQSO does AI automation consulting. Hours: M-F 9-6 CT. Web: aiqso.io
For appointments, suggest calling (855) 301-1227 or visiting our website."""

# Greeting variations - using spelled out name for TTS
GREETINGS = {
    "standard": "Hello! Thank you for calling A. I. Q. S. O. I'm your AI assistant. How can I help you today?",
    "returning": "Welcome back to A. I. Q. S. O.! Great to hear from you again. How can I help you today?",
    "after_hours": "Thank you for calling A. I. Q. S. O. Our office is currently closed, but I can still help with questions or schedule a callback for you. What would you like to do?",
}

# Common response templates
RESPONSES = {
    "schedule_appointment": "I'd be happy to schedule a consultation for you. Let me check our availability.",
    "services_overview": "AIQSO specializes in AI automation. We help businesses automate workflows, integrate AI into existing systems, and develop custom AI solutions. Would you like to learn more about a specific service?",
    "pricing": "Our pricing is customized based on your specific needs. I'd recommend scheduling a free consultation where we can discuss your requirements and provide a detailed quote. Would you like me to set that up?",
    "human_transfer": "I understand you'd like to speak with someone directly. Let me take your information and have a team member call you back within the hour.",
    "not_understood": "I'm sorry, I didn't quite catch that. Could you please repeat what you said?",
    "goodbye": "Thank you for calling AIQSO. Have a great day!",
}

# Intent patterns for routing
INTENT_PATTERNS = {
    "schedule": ["appointment", "schedule", "book", "meet", "consultation", "call back", "available"],
    "services": ["services", "offer", "do you", "what do you", "help with", "provide"],
    "pricing": ["price", "cost", "how much", "quote", "rate", "fee"],
    "hours": ["hours", "open", "close", "when are you"],
    "location": ["where", "located", "address", "office"],
    "human": ["person", "human", "representative", "someone", "agent", "speak to"],
    "existing_customer": ["my appointment", "my account", "my project", "status"],
}


def get_service_description(service_name: str) -> str:
    """Get a detailed description of a specific service."""
    for service in AIQSO_SERVICES:
        if service_name.lower() in service["name"].lower():
            examples = ", ".join(service["examples"])
            return f"{service['description']}. For example: {examples}."
    return "We offer various AI automation and consulting services. Would you like me to explain our main offerings?"


def detect_intent(query: str) -> str:
    """Detect the caller's intent from their query."""
    query_lower = query.lower()

    for intent, patterns in INTENT_PATTERNS.items():
        if any(pattern in query_lower for pattern in patterns):
            return intent

    return "general"


def get_contextual_prompt(caller_info: dict = None, call_context: str = None) -> str:
    """
    Get a contextual system prompt based on caller info and context.

    Args:
        caller_info: Dict with caller details (name, is_customer, etc.)
        call_context: Context like "after_hours", "returning", etc.

    Returns:
        str: Customized system prompt
    """
    base_prompt = VOICE_SYSTEM_PROMPT

    # Add caller context if available
    if caller_info:
        name = caller_info.get("name", "the caller")
        base_prompt += f"\n\nCurrent caller: {name}"

        if caller_info.get("is_customer"):
            base_prompt += "\nThis is an existing customer - be extra helpful and personalized."

        if caller_info.get("notes"):
            base_prompt += f"\nPrevious notes: {caller_info['notes']}"

    # Add time-based context
    if call_context == "after_hours":
        base_prompt += "\n\nNote: It's currently outside business hours. Offer to schedule a callback."

    return base_prompt
