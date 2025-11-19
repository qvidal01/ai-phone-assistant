# Examples

This directory contains example code demonstrating how to use the AI Phone Assistant.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)

Demonstrates the fundamental features:
- Loading configuration
- Initializing the PhoneAssistant
- Making outbound calls
- Sending SMS notifications

```bash
python examples/basic_usage.py
```

### 2. CRM Integration (`crm_usage.py`)

Shows how to work with the CRM system:
- Creating and managing customer records
- Scheduling appointments
- Adding notes to customer records
- Updating and canceling appointments

```bash
python examples/crm_usage.py
```

### 3. Running the Server (`run_server.py`)

Starts the FastAPI server to handle Twilio webhooks:
- Incoming call handling
- Speech processing
- Call status callbacks
- SMS handling

```bash
python examples/run_server.py
```

Or use the main entry point:

```bash
python main.py --server
```

## Prerequisites

Before running the examples, make sure you have:

1. Installed all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Created a `.env` file with your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Set up required API keys:
   - Anthropic API key for Claude
   - Twilio account credentials

## Notes

- The `basic_usage.py` example has actual call/SMS code commented out to prevent accidental charges
- The `crm_usage.py` example uses MockCRM (in-memory storage) for demonstration
- For production use, implement a real CRM integration by extending `CRMBase`

## Twilio Webhook Configuration

When running the server, configure your Twilio phone number webhooks to point to:

- **Voice URL**: `https://your-domain.com/voice/incoming` (POST)
- **Status Callback URL**: `https://your-domain.com/voice/status` (POST)
- **SMS URL**: `https://your-domain.com/sms/incoming` (POST)

For local development, use a tool like [ngrok](https://ngrok.com/) to expose your local server:

```bash
# In one terminal
python main.py --server

# In another terminal
ngrok http 8000
```

Then use the ngrok URL in your Twilio webhook configuration.
