# AI Phone Assistant - Claude Reference

## Quick Overview
Voice/phone AI assistant for automating business calls with **smart multi-backend AI routing**. Handles status inquiries, appointment scheduling, and CRM integration using Twilio with your choice of Claude API or local Ollama models.

## Tech Stack
- **Framework:** FastAPI + Uvicorn
- **Language:** Python 3.9+
- **Voice:** Twilio (voice/SMS)
- **AI Backends:**
  - Ollama (local) - HP840 server at 192.168.0.234
  - Claude API (cloud) - Anthropic
- **Database:** SQLAlchemy
- **Cache:** Redis

## Project Structure
```
src/
├── assistant/
│   ├── phone_assistant.py   # Main orchestrator
│   ├── claude_handler.py    # Claude API integration
│   ├── ollama_handler.py    # Local Ollama integration
│   └── ai_router.py         # Smart backend routing
├── integrations/            # CRM & calendar integrations
├── voice/                   # Twilio voice handling
├── utils/                   # Config and helpers
└── server.py                # FastAPI webhook server

tests/                       # Unit & integration tests
docs/                        # Documentation
examples/                    # Usage examples
main.py                      # CLI entry point
```

## Smart AI Routing

The system automatically routes queries to the optimal backend:

| Query Type | Backend | Model | Latency |
|------------|---------|-------|---------|
| Simple (greetings, yes/no) | Ollama | quick-responder | ~500ms |
| Moderate (status, scheduling) | Ollama | cyberque-chat | ~2-3s |
| Complex (reasoning, multi-step) | Ollama/Claude | llama3.3:70b or Claude | ~3-5s |

### Routing Logic
- Analyzes query complexity via pattern matching
- Prefers local Ollama to save API costs
- Falls back to Claude if Ollama fails
- Tracks usage stats per backend

## Quick Commands
```bash
# Start server mode
python main.py --server

# With uvicorn directly
uvicorn src.server:app --reload --port 8000

# Test routing (after server starts)
curl -X POST http://localhost:8000/api/test -d "message=Hello"
```

## API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check with backend status |
| `/health` | GET | Detailed health check |
| `/stats` | GET | Usage statistics per backend |
| `/voice/incoming` | POST | Twilio incoming call webhook |
| `/voice/process` | POST | Process speech input |
| `/voice/status` | POST | Call status callback |
| `/sms/incoming` | POST | SMS webhook |
| `/api/test` | POST | Test query routing |

## Key Features
- **Multi-Backend AI:** Smart routing between local and cloud
- **Cost Optimization:** Prefers free local models when appropriate
- **Automatic Fallback:** Switches to Claude if Ollama fails
- **Natural Language:** Handles conversational phone interactions
- **CRM Integration:** Logs calls to Salesforce, HubSpot, etc.
- **Appointment Scheduling:** Calendar integration ready
- **SMS Support:** Automated text responses
- **Usage Analytics:** Track backend usage and costs

## Environment Variables
```bash
# AI Backends
ANTHROPIC_API_KEY=           # Claude API (optional)
OLLAMA_URL=http://192.168.0.234:11434
OLLAMA_DEFAULT_MODEL=quick-responder:latest
OLLAMA_SMART_MODEL=llama3.3:70b
OLLAMA_CHAT_MODEL=cyberque-chat:latest
PREFER_LOCAL_AI=true

# Twilio (required)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Optional
CRM_API_KEY=
CRM_API_URL=
BUSINESS_NAME=
BUSINESS_TYPE=auto_shop
```

## Ollama Models Available
| Model | Size | Use Case |
|-------|------|----------|
| quick-responder | 3.2B | Fast simple queries |
| cyberque-chat | 7.6B | General conversation |
| general-assistant | 7.2B | Balanced responses |
| llama3.3:70b | 70B | Complex reasoning |

## Twilio Webhooks
Configure in Twilio console:
- Voice URL: `https://your-domain/voice/incoming`
- Voice Status: `https://your-domain/voice/status`
- SMS URL: `https://your-domain/sms/incoming`

## Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run server
python main.py --server --port 8000
```

## Status
**v2.0.0** - Multi-backend AI routing implemented
- Smart query routing
- Ollama local integration
- Usage statistics
- Automatic fallback
