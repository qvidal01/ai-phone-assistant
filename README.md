# 📞 AI Phone Assistant

Open-source AI-powered phone assistant that handles customer inquiries, appointments, and status updates. Integrates with popular CRM and scheduling systems.

## 🌟 Features

- **Natural Language Understanding** - Powered by Claude AI for human-like conversations
- **CRM Integration** - Works with Salesforce, HubSpot, and custom CRMs
- **Appointment Scheduling** - Automatic calendar management and booking
- **SMS Notifications** - Send automated status updates to customers
- **Multi-language Support** - Handle calls in multiple languages
- **Call Analytics** - Track call metrics and customer satisfaction

## 🚀 Quick Start

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

### Configuration

Create a `.env` file with the following variables:

```env
ANTHROPIC_API_KEY=your_claude_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number
CRM_API_KEY=your_crm_api_key
```

### Usage

```python
from ai_phone_assistant import PhoneAssistant

# Initialize the assistant
assistant = PhoneAssistant()

# Start receiving calls
assistant.start()
```

## 📋 Use Cases

- **Auto Shops** - "Is my car ready?" status inquiries
- **Salons & Spas** - Appointment booking and reminders
- **Service Businesses** - Schedule service calls
- **Medical Offices** - Patient appointment management

## 🛠️ Development

### Project Structure

```
ai-phone-assistant/
├── src/
│   ├── assistant/       # Core AI assistant logic
│   ├── integrations/    # CRM and calendar integrations
│   ├── voice/          # Voice processing
│   └── utils/          # Helper functions
├── tests/              # Unit and integration tests
├── docs/               # Documentation
└── examples/           # Example implementations
```

### Running Tests

```bash
pytest tests/
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/) for natural language understanding
- Phone integration powered by [Twilio](https://www.twilio.com/)
- Maintained by [AIQSO](https://aiqso.io)

## 📞 Support

- 📧 Email: support@aiqso.io
- 🐛 Issues: [GitHub Issues](https://github.com/qvidal01/ai-phone-assistant/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/qvidal01/ai-phone-assistant/discussions)

---

Made with ❤️ by [AIQSO](https://aiqso.io)
