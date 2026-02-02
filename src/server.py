"""FastAPI server for handling Twilio webhooks."""

from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import Response

from src.assistant.phone_assistant import PhoneAssistant
from src.utils.logger import setup_logger

# Initialize FastAPI app
app = FastAPI(
    title="AI Phone Assistant API",
    description="Multi-backend AI phone assistant with smart routing",
    version="2.0.0",
)

# Initialize phone assistant
assistant = PhoneAssistant()

# Logger
logger = setup_logger(__name__)


@app.get("/")
async def root():
    """Health check endpoint."""
    availability = assistant.ai_router.check_backend_availability()
    return {
        "status": "online",
        "service": "AI Phone Assistant",
        "version": "2.0.0",
        "backends": {
            "ollama": "online" if availability.get("ollama") else "offline",
            "claude": "configured" if availability.get("claude") else "not_configured",
        },
        "routing_strategy": "smart",
        "prefer_local": assistant.ai_router.prefer_local,
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    availability = assistant.ai_router.check_backend_availability()
    return {
        "status": "healthy",
        "backends": availability,
        "active_calls": len(assistant.active_calls),
    }


@app.get("/stats")
async def get_stats():
    """Get usage statistics."""
    return assistant.get_stats()


@app.post("/voice/incoming")
async def handle_incoming_call(
    request: Request,
    From: str = Form(...),
    To: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None),
):
    """
    Handle incoming phone calls from Twilio.

    Args:
        From: Caller's phone number
        To: Called phone number
        CallSid: Unique call identifier

    Returns:
        TwiML response
    """
    logger.info(f"Incoming call from {From} (CallSid: {CallSid})")

    try:
        twiml_response = assistant.handle_incoming_call(caller_number=From)
        return Response(content=twiml_response, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        # Return a basic error response
        error_twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>We are experiencing technical difficulties. Please try again later.</Say><Hangup/></Response>'
        return Response(content=error_twiml, media_type="application/xml")


@app.post("/voice/process")
async def process_voice_input(
    request: Request,
    From: str = Form(...),
    SpeechResult: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None),
):
    """
    Process speech input from caller.

    Args:
        From: Caller's phone number
        SpeechResult: Transcribed speech from caller
        CallSid: Unique call identifier

    Returns:
        TwiML response
    """
    logger.info(f"Processing speech from {From}: {SpeechResult}")

    try:
        if not SpeechResult:
            # No speech detected
            twiml_response = assistant.twilio.create_response_twiml(
                message="I didn't catch that. Could you please repeat?", continue_conversation=True
            )
        else:
            twiml_response = assistant.process_speech(caller_number=From, speech_text=SpeechResult)

        return Response(content=twiml_response, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error processing speech: {e}")
        error_twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>I apologize, but I encountered an error. Please try again.</Say><Redirect>/voice/process</Redirect></Response>'
        return Response(content=error_twiml, media_type="application/xml")


@app.post("/voice/status")
async def call_status_callback(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    From: Optional[str] = Form(None),
):
    """
    Handle call status callbacks from Twilio.

    Args:
        CallSid: Unique call identifier
        CallStatus: Current call status
        From: Caller's phone number

    Returns:
        Success response
    """
    logger.info(f"Call status update - CallSid: {CallSid}, Status: {CallStatus}")

    # Clean up when call ends
    if CallStatus in ["completed", "busy", "no-answer", "failed", "canceled"]:
        if From:
            try:
                assistant.end_call(caller_number=From)
            except Exception as e:
                logger.error(f"Error ending call: {e}")

    return {"status": "received"}


@app.post("/sms/incoming")
async def handle_incoming_sms(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
):
    """
    Handle incoming SMS messages.

    Args:
        From: Sender's phone number
        Body: SMS message content
        MessageSid: Unique message identifier

    Returns:
        TwiML response
    """
    logger.info(f"Incoming SMS from {From}: {Body}")

    try:
        # Process SMS with smart routing
        response, decision = assistant.ai_router.generate_response(
            query=Body,
            system_prompt=(
                "You are a helpful SMS assistant. Provide brief, "
                "concise responses suitable for text messaging. "
                "Keep responses under 160 characters when possible."
            ),
        )

        logger.info(f"SMS routed to {decision.backend.value}")

        # Send SMS response
        assistant.send_sms_notification(to_number=From, message=response)

        return {"status": "processed", "backend": decision.backend.value}
    except Exception as e:
        logger.error(f"Error handling SMS: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/test")
async def test_routing(message: str = Form(...)):
    """
    Test endpoint to see how a message would be routed.

    Args:
        message: Test message

    Returns:
        Routing decision and response
    """
    try:
        response, decision = assistant.ai_router.generate_response(query=message)
        return {
            "message": message,
            "response": response,
            "backend": decision.backend.value,
            "model": decision.model,
            "complexity": decision.complexity.value,
            "reason": decision.reason,
        }
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting AI Phone Assistant server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
