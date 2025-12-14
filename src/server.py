"""FastAPI server for handling Twilio webhooks with security validation."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, Request, HTTPException, Depends
from fastapi.responses import Response
from typing import Optional
from twilio.request_validator import RequestValidator
from src.assistant.phone_assistant import PhoneAssistant
from src.utils.config import load_config, mask_phone_number, __version__
from src.utils.logger import setup_logger

# Initialize configuration and logger first
config = load_config()
logger = setup_logger(__name__, level=config.log_level)

# Twilio request validator for webhook security
twilio_validator = RequestValidator(config.twilio_auth_token)


def get_assistant() -> PhoneAssistant:
    """Dependency to get the phone assistant instance."""
    return app.state.assistant


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting AI Phone Assistant server...")
    app.state.assistant = PhoneAssistant(config=config)
    logger.info(f"Server initialized. Phone number: {mask_phone_number(config.twilio_phone_number)}")
    yield
    # Shutdown
    logger.info("Shutting down AI Phone Assistant server...")


# Initialize FastAPI app with lifespan management
app = FastAPI(
    title="AI Phone Assistant API",
    version=__version__,
    description="AI-powered phone assistant handling customer inquiries",
    lifespan=lifespan,
)


async def validate_twilio_request(request: Request) -> bool:
    """
    Validate that incoming requests are from Twilio.

    In production, enable this by setting VALIDATE_TWILIO_REQUESTS=true.
    """
    # Skip validation in debug mode or if explicitly disabled
    if config.debug or os.getenv("VALIDATE_TWILIO_REQUESTS", "false").lower() != "true":
        return True

    # Get the full URL that was requested
    url = str(request.url)

    # Get the Twilio signature from headers
    signature = request.headers.get("X-Twilio-Signature", "")

    # Get form data
    form_data = await request.form()
    params = {key: value for key, value in form_data.items()}

    # Validate the request
    is_valid = twilio_validator.validate(url, params, signature)

    if not is_valid:
        logger.warning("Invalid Twilio signature detected - possible spoofed request")
        raise HTTPException(status_code=403, detail="Invalid request signature")

    return True


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "AI Phone Assistant",
        "version": __version__
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "components": {
            "server": "online",
            "phone_number_configured": bool(config.twilio_phone_number),
            "claude_configured": bool(config.anthropic_api_key),
        }
    }


@app.post("/voice/incoming")
async def handle_incoming_call(
    request: Request,
    From: str = Form(...),
    To: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None),
    _: bool = Depends(validate_twilio_request),
    assistant: PhoneAssistant = Depends(get_assistant)
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
    # Log with masked phone number for PII protection
    logger.info(f"Incoming call from {mask_phone_number(From)} (CallSid: {CallSid})")

    try:
        twiml_response = assistant.handle_incoming_call(caller_number=From)
        return Response(content=twiml_response, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}", exc_info=config.debug)
        # Return a basic error response
        error_twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>We are experiencing technical difficulties. Please try again later.</Say><Hangup/></Response>'
        return Response(content=error_twiml, media_type="application/xml")


@app.post("/voice/process")
async def process_voice_input(
    request: Request,
    From: str = Form(...),
    SpeechResult: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None),
    _: bool = Depends(validate_twilio_request),
    assistant: PhoneAssistant = Depends(get_assistant)
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
    # Log with masked phone number, truncate speech for log readability
    speech_preview = SpeechResult[:50] + "..." if SpeechResult and len(SpeechResult) > 50 else SpeechResult
    logger.info(f"Processing speech from {mask_phone_number(From)}: {speech_preview}")

    try:
        if not SpeechResult:
            # No speech detected
            twiml_response = assistant.twilio.create_response_twiml(
                message="I didn't catch that. Could you please repeat?",
                continue_conversation=True
            )
        else:
            twiml_response = assistant.process_speech(
                caller_number=From,
                speech_text=SpeechResult
            )

        return Response(content=twiml_response, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error processing speech: {e}", exc_info=config.debug)
        error_twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>I apologize, but I encountered an error. Please try again.</Say><Redirect>/voice/process</Redirect></Response>'
        return Response(content=error_twiml, media_type="application/xml")


@app.post("/voice/status")
async def call_status_callback(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    From: Optional[str] = Form(None),
    _: bool = Depends(validate_twilio_request),
    assistant: PhoneAssistant = Depends(get_assistant)
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
                logger.error(f"Error ending call: {e}", exc_info=config.debug)

    return {"status": "received"}


@app.post("/sms/incoming")
async def handle_incoming_sms(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
    _: bool = Depends(validate_twilio_request),
    assistant: PhoneAssistant = Depends(get_assistant)
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
    # Log with masked phone number, truncate body for privacy
    body_preview = Body[:30] + "..." if len(Body) > 30 else Body
    logger.info(f"Incoming SMS from {mask_phone_number(From)}: {body_preview}")

    try:
        # Process SMS with Claude
        response = assistant.claude.generate_response(
            user_message=Body,
            system_prompt=(
                "You are a helpful SMS assistant. Provide brief, "
                "concise responses suitable for text messaging. "
                "Keep responses under 160 characters when possible."
            )
        )

        # Send SMS response
        assistant.send_sms_notification(to_number=From, message=response)

        return {"status": "processed"}
    except Exception as e:
        logger.error(f"Error handling SMS: {e}", exc_info=config.debug)
        # Don't expose internal error details
        return {"status": "error", "message": "Failed to process message"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting AI Phone Assistant server...")
    uvicorn.run(
        app,
        host=config.server_host,
        port=config.server_port,
        log_level=config.log_level.lower()
    )
