# Contributing to AI Phone Assistant

Thank you for your interest in contributing to AI Phone Assistant! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:
- Clear description of the feature
- Use case and benefits
- Any implementation ideas

### Pull Requests

1. **Fork the repository**
   ```bash
   git fork https://github.com/qvidal01/ai-phone-assistant.git
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clear, documented code
   - Follow the existing code style
   - Add tests for new features
   - Update documentation as needed

4. **Run tests**
   ```bash
   pytest tests/
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add feature: your feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure all tests pass

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/qvidal01/ai-phone-assistant.git
   cd ai-phone-assistant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your test credentials
   ```

5. **Run tests**
   ```bash
   pytest tests/
   ```

## Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and concise
- Add type hints where appropriate

### Example

```python
def create_customer(self, customer_data: Dict) -> Dict:
    """
    Create a new customer record.

    Args:
        customer_data: Customer information dictionary

    Returns:
        Dict: Created customer data with ID

    Raises:
        ValueError: If required fields are missing
    """
    # Implementation here
```

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for good test coverage
- Use pytest fixtures for common setup

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_config.py

# Run with coverage
pytest --cov=src tests/
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions/classes
- Update examples if adding new features
- Create documentation in `docs/` for complex features

## CRM Integrations

To add a new CRM integration:

1. Create a new file in `src/integrations/`
2. Extend the `CRMBase` class
3. Implement all abstract methods
4. Add tests in `tests/`
5. Create an example in `examples/`
6. Document the integration

Example:

```python
from src.integrations.crm_base import CRMBase

class SalesforceCRM(CRMBase):
    """Salesforce CRM integration."""

    def __init__(self, api_key: str, instance_url: str):
        # Implementation
        pass

    def get_customer(self, phone_number: str) -> Optional[Dict]:
        # Implementation
        pass

    # ... implement other methods
```

## Questions?

If you have questions, feel free to:
- Open an issue for discussion
- Contact the maintainers
- Check existing issues and PRs

Thank you for contributing! 🎉
