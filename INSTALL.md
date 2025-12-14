# Installation Guide

This guide covers installation and deployment of the AI Phone Assistant.

## Prerequisites

- **Python 3.9+** - Required runtime
- **Anthropic API Key** - Get from [console.anthropic.com](https://console.anthropic.com/)
- **Twilio Account** - Get from [twilio.com](https://www.twilio.com/console)
  - Account SID
  - Auth Token
  - Phone Number with Voice/SMS capabilities

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/qvidal01/ai-phone-assistant.git
cd ai-phone-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your credentials
nano .env  # or your preferred editor
```

Required configuration:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-your_api_key_here
TWILIO_ACCOUNT_SID=ACyour_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+14155551234
```

### 3. Run the Server

```bash
# Development mode
python main.py --server

# Or directly with uvicorn
uvicorn src.server:app --host 0.0.0.0 --port 8000
```

### 4. Configure Twilio Webhooks

1. Go to [Twilio Console](https://console.twilio.com/) > Phone Numbers
2. Select your phone number
3. Configure webhooks:
   - **Voice URL**: `https://your-domain.com/voice/incoming` (POST)
   - **Status Callback URL**: `https://your-domain.com/voice/status` (POST)
   - **SMS URL**: `https://your-domain.com/sms/incoming` (POST)

## Local Development with ngrok

For local development, use [ngrok](https://ngrok.com/) to expose your local server:

```bash
# Terminal 1: Start the server
python main.py --server --port 8000

# Terminal 2: Start ngrok
ngrok http 8000
```

Use the ngrok HTTPS URL in your Twilio webhook configuration.

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t ai-phone-assistant .
docker run -p 8000:8000 --env-file .env ai-phone-assistant
```

### Production Configuration

For production deployments, ensure:

1. **Enable Twilio Webhook Validation**:
   ```env
   VALIDATE_TWILIO_REQUESTS=true
   ```

2. **Set Appropriate Log Level**:
   ```env
   LOG_LEVEL=WARNING
   DEBUG=false
   ```

3. **Use HTTPS**: Twilio requires HTTPS for webhooks

4. **Set Up Health Checks**: Monitor `/health` endpoint

### Deployment Checklist

- [ ] All required environment variables set
- [ ] HTTPS configured (required for Twilio)
- [ ] Twilio webhook URLs configured and verified
- [ ] `VALIDATE_TWILIO_REQUESTS=true` enabled
- [ ] Health check monitoring configured
- [ ] Log aggregation set up
- [ ] Error alerting configured

## Verification

### Test the Server

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"0.1.0","components":{"server":"online",...}}
```

### Test with Twilio

1. Call your Twilio phone number
2. You should hear the AI greeting
3. Speak to test the conversation flow

## Troubleshooting

### Common Issues

**Configuration Errors at Startup**

```
Configuration error: ANTHROPIC_API_KEY is required...
```

Solution: Ensure all required environment variables are set in `.env`

**Twilio Webhook Errors**

```
Invalid request signature
```

Solution: Verify your Twilio Auth Token is correct, or disable validation for testing:
```env
VALIDATE_TWILIO_REQUESTS=false
```

**No Speech Recognition**

Ensure:
- Caller is speaking clearly
- `VOICE_LANGUAGE` matches caller's language
- Phone audio quality is sufficient

### Getting Help

- Check logs for detailed error messages
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system understanding
- Open an issue on [GitHub](https://github.com/qvidal01/ai-phone-assistant/issues)
