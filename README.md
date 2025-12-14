# AI Phone Assistant

Open-source AI-powered phone assistant that handles customer inquiries, appointments, and status updates. Integrates with popular CRM and scheduling systems.

## Features

- **Natural Language Understanding** - Powered by Claude AI for human-like conversations
- **CRM Integration** - Works with Salesforce, HubSpot, and custom CRMs
- **Appointment Scheduling** - Automatic calendar management and booking
- **SMS Notifications** - Send automated status updates to customers
- **Multi-language Support** - Handle calls in multiple languages
- **Call Analytics** - Track call metrics and customer satisfaction
- **Security** - PII protection, webhook validation, and secure configuration

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Anthropic API key for Claude AI
- Twilio account for phone integration

### Installation

```bash
# Clone the repository
git clone https://github.com/qvidal01/ai-phone-assistant.git
cd ai-phone-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

### Configuration

Create a `.env` file with the following variables:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-your_api_key_here
TWILIO_ACCOUNT_SID=ACyour_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+14155551234

# Optional
LOG_LEVEL=INFO
DEBUG=false
```

See [.env.example](.env.example) for all configuration options.

### Usage

**Start the server:**

```bash
python main.py --server
```

**Programmatic usage:**

```python
from src.assistant.phone_assistant import PhoneAssistant
from src.utils.config import load_config

# Load configuration
config = load_config()

# Initialize the assistant
assistant = PhoneAssistant(config=config)

# The assistant is now ready to handle calls via webhooks
```

## Use Cases

- **Auto Shops** - "Is my car ready?" status inquiries
- **Salons & Spas** - Appointment booking and reminders
- **Service Businesses** - Schedule service calls
- **Medical Offices** - Patient appointment management

## Documentation

- [Architecture Overview](ARCHITECTURE.md) - System design and component descriptions
- [Installation Guide](INSTALL.md) - Detailed setup and deployment instructions
- [Changelog](CHANGELOG.md) - Version history and changes
- [Implementation Notes](IMPLEMENTATION_NOTES.md) - Technical decisions and rationale
- [Contributing Guide](CONTRIBUTING.md) - How to contribute

## Development

### Project Structure

```
ai-phone-assistant/
├── src/
│   ├── assistant/       # Core AI assistant logic
│   ├── integrations/    # CRM and calendar integrations
│   ├── voice/           # Voice processing
│   ├── utils/           # Helper functions
│   └── server.py        # FastAPI webhook server
├── tests/               # Unit and integration tests
├── examples/            # Example implementations
├── main.py              # CLI entry point
└── requirements.txt     # Python dependencies
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_config.py -v
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health status |
| `/voice/incoming` | POST | Handle incoming calls |
| `/voice/process` | POST | Process speech input |
| `/voice/status` | POST | Call status callbacks |
| `/sms/incoming` | POST | Handle incoming SMS |

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/) for natural language understanding
- Phone integration powered by [Twilio](https://www.twilio.com/)
- Maintained by [AIQSO](https://aiqso.io)

## Support

- Issues: [GitHub Issues](https://github.com/qvidal01/ai-phone-assistant/issues)
- Discussions: [GitHub Discussions](https://github.com/qvidal01/ai-phone-assistant/discussions)

---

Made with care by [AIQSO](https://aiqso.io)
