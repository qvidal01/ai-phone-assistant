# Architecture Overview

This document describes the high-level architecture of the AI Phone Assistant system.

## System Overview

The AI Phone Assistant is a Python-based service that handles phone calls and SMS messages using AI-powered natural language processing. It integrates with Twilio for voice/SMS capabilities and Anthropic's Claude for conversation intelligence.

```
                                    +------------------+
                                    |   Twilio Cloud   |
                                    | (Voice + SMS)    |
                                    +--------+---------+
                                             |
                                             | Webhooks (HTTPS)
                                             v
+-------------------+              +------------------+
|   Phone/SMS       |   <---->     |   FastAPI        |
|   Users           |              |   Server         |
+-------------------+              +--------+---------+
                                             |
                         +-------------------+-------------------+
                         |                   |                   |
                         v                   v                   v
               +----------------+  +------------------+  +---------------+
               | TwilioHandler  |  | PhoneAssistant   |  | ClaudeHandler |
               | (Voice/SMS)    |  | (Orchestrator)   |  | (AI)          |
               +----------------+  +--------+---------+  +---------------+
                                             |
                                             v
                                   +------------------+
                                   |   CRM Integration|
                                   |   (Pluggable)    |
                                   +------------------+
```

## Core Components

### 1. FastAPI Server (`src/server.py`)

The HTTP server that handles Twilio webhooks:

- **`/voice/incoming`** - Receives incoming call webhooks, initiates AI conversation
- **`/voice/process`** - Processes speech-to-text results and generates responses
- **`/voice/status`** - Handles call status callbacks (completed, failed, etc.)
- **`/sms/incoming`** - Handles incoming SMS messages
- **`/health`** - Health check endpoint for monitoring

**Security Features:**
- Twilio request signature validation (optional, enable with `VALIDATE_TWILIO_REQUESTS=true`)
- PII masking in all logs
- Proper error handling without leaking internal details

### 2. PhoneAssistant (`src/assistant/phone_assistant.py`)

The main orchestrator that coordinates all components:

- Manages active call state
- Routes incoming calls to appropriate handlers
- Coordinates between Claude AI and Twilio
- Logs interactions to CRM
- Tracks call metrics (duration, interaction count)

### 3. ClaudeHandler (`src/assistant/claude_handler.py`)

Handles all interactions with Claude AI:

- Maintains conversation history per call
- Generates contextual responses
- Creates conversation summaries at call end
- Handles API errors gracefully with user-friendly messages
- Prevents memory leaks via conversation history trimming

### 4. TwilioHandler (`src/voice/twilio_handler.py`)

Manages Twilio voice and SMS operations:

- Creates TwiML responses for voice calls
- Handles speech recognition configuration
- Makes outbound calls
- Sends SMS messages
- Retrieves call status

### 5. CRM Integration (`src/integrations/`)

Pluggable CRM integration system:

- **`CRMBase`** - Abstract base class defining the CRM interface
- **`MockCRM`** - In-memory implementation for testing/development
- Extensible for Salesforce, HubSpot, or custom CRM systems

## Data Flow

### Incoming Call Flow

```
1. Phone Call → Twilio Cloud
2. Twilio → POST /voice/incoming (webhook)
3. Server → PhoneAssistant.handle_incoming_call()
4. PhoneAssistant → CRM.get_customer() (lookup caller)
5. PhoneAssistant → TwilioHandler.create_greeting_response()
6. Server → Return TwiML (greeting + gather speech)
7. Caller speaks → Twilio transcribes
8. Twilio → POST /voice/process (speech result)
9. Server → PhoneAssistant.process_speech()
10. PhoneAssistant → ClaudeHandler.generate_response()
11. PhoneAssistant → TwilioHandler.create_response_twiml()
12. Server → Return TwiML (AI response + gather speech)
... repeat 7-12 until conversation ends ...
13. Twilio → POST /voice/status (call completed)
14. Server → PhoneAssistant.end_call()
15. PhoneAssistant → ClaudeHandler.get_conversation_summary()
16. PhoneAssistant → CRM.create_note() (log summary)
```

### SMS Flow

```
1. SMS → Twilio Cloud
2. Twilio → POST /sms/incoming
3. Server → ClaudeHandler.generate_response()
4. Server → TwilioHandler.send_sms()
5. Server → Return success
```

## Configuration

Configuration is managed via environment variables loaded through Pydantic:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude AI API key |
| `TWILIO_ACCOUNT_SID` | Yes | Twilio account identifier |
| `TWILIO_AUTH_TOKEN` | Yes | Twilio authentication token |
| `TWILIO_PHONE_NUMBER` | Yes | Your Twilio phone number |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `VALIDATE_TWILIO_REQUESTS` | No | Enable webhook signature validation |

See `.env.example` for full configuration options.

## Security Considerations

1. **PII Protection**: All phone numbers are masked in logs using `mask_phone_number()`
2. **Webhook Validation**: Twilio request signatures can be validated
3. **Configuration Validation**: All required fields are validated at startup
4. **Error Handling**: Internal errors are not exposed to external callers
5. **Rate Limiting**: Claude API rate limits are handled gracefully

## Extensibility

### Adding a New CRM Integration

1. Create a new file in `src/integrations/`
2. Inherit from `CRMBase`
3. Implement all abstract methods
4. Pass the CRM instance to `PhoneAssistant(crm=YourCRM())`

### Customizing AI Behavior

- Modify `_build_system_prompt()` in `PhoneAssistant` for custom prompts
- Adjust `max_tokens` in `ClaudeHandler.generate_response()` for response length
- Configure `SPEECH_TIMEOUT` and `VOICE_LANGUAGE` for speech recognition

## Performance Considerations

- Conversation history is trimmed to prevent unbounded memory growth
- FastAPI provides async support for concurrent call handling
- Logging is optimized to avoid blocking I/O operations

## Monitoring

- Use `/health` endpoint for service health checks
- All operations are logged with appropriate levels
- Call metrics (duration, interaction count) are tracked per session
