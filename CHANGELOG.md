# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-12-14

### Security

- **PII Protection**: All phone numbers are now masked in logs using `mask_phone_number()` function
- **Webhook Validation**: Added optional Twilio request signature validation (enable with `VALIDATE_TWILIO_REQUESTS=true`)
- **Configuration Validation**: Added validators for API keys, account SIDs, and phone numbers
  - Anthropic API keys must start with `sk-ant-`
  - Twilio Account SIDs must start with `AC`
  - Phone numbers must be in E.164 format
- **Error Handling**: Internal error details are no longer exposed in API responses

### Added

- New configuration options:
  - `SERVER_HOST` and `SERVER_PORT` for server binding
  - `SPEECH_TIMEOUT` and `VOICE_LANGUAGE` for voice recognition
  - `VALIDATE_TWILIO_REQUESTS` for webhook security
- `/health` endpoint for detailed health checks
- `mask_phone_number()` and `mask_sensitive_string()` utility functions
- Conversation history trimming to prevent unbounded memory growth (max 50 messages)
- Call duration tracking and interaction counting
- Comprehensive test suite for configuration, Claude handler, and server endpoints

### Changed

- Updated Pydantic configuration to v2 style (`model_config` instead of inner `Config` class)
- Claude handler now handles specific API errors (RateLimitError, APIConnectionError, APIError)
- Server now uses FastAPI lifespan management for proper startup/shutdown
- Improved error messages for configuration validation failures
- Updated default Claude model to `claude-sonnet-4-20250514`
- TwilioHandler now accepts configurable speech timeout and language settings

### Removed

- Removed unused dependencies: `redis>=5.0.0`, `sqlalchemy>=2.0.0`
- Removed hardcoded version strings (now centralized in `src/utils/config.py`)

### Fixed

- Fixed potential memory leak in conversation history (now trimmed automatically)
- Fixed error rollback in Claude handler when API calls fail
- Fixed inconsistent error handling across server endpoints

### Documentation

- Added `ARCHITECTURE.md` with system design documentation
- Added `INSTALL.md` with detailed installation instructions
- Added `CHANGELOG.md` (this file)
- Added `IMPLEMENTATION_NOTES.md` with technical decisions
- Updated `.env.example` with all configuration options

## [0.1.0] - 2024-12-01

### Added

- Initial release
- Core phone assistant functionality
- Claude AI integration for natural language processing
- Twilio integration for voice calls and SMS
- FastAPI server for webhook handling
- Mock CRM implementation for testing
- Basic configuration management
- Example scripts for usage demonstration
