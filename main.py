#!/usr/bin/env python
"""Main entry point for AI Phone Assistant."""

import argparse
import sys

from src.utils.config import load_config
from src.utils.logger import setup_logger


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI Phone Assistant - Intelligent phone call handling"
    )
    parser.add_argument(
        "--server", action="store_true", help="Start the web server for handling Twilio webhooks"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config()
        logger = setup_logger("main", level=config.log_level)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file with required API keys")
        print("2. Set all required environment variables")
        print("\nSee .env.example for reference.")
        return 1

    if args.server:
        # Start web server
        import uvicorn

        from src.server import app

        logger.info(f"Starting server on {args.host}:{args.port}")
        print(f"\n{'=' * 60}")
        print("AI Phone Assistant Server")
        print(f"{'=' * 60}")
        print(f"\nServer running on http://{args.host}:{args.port}")
        print(f"Phone Number: {config.twilio_phone_number}")
        print("\nWebhook Endpoints:")
        print(f"  - Incoming Calls: http://{args.host}:{args.port}/voice/incoming")
        print(f"  - Voice Processing: http://{args.host}:{args.port}/voice/process")
        print(f"  - Call Status: http://{args.host}:{args.port}/voice/status")
        print(f"  - Incoming SMS: http://{args.host}:{args.port}/sms/incoming")
        print(f"\n{'=' * 60}\n")

        try:
            uvicorn.run(app, host=args.host, port=args.port, log_level=config.log_level.lower())
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            return 0
    else:
        # Interactive mode
        from src.assistant.phone_assistant import PhoneAssistant

        print(f"\n{'=' * 60}")
        print("AI Phone Assistant")
        print(f"{'=' * 60}")
        print(f"\nPhone Number: {config.twilio_phone_number}")
        print("\nOptions:")
        print("  --server    Start web server for handling calls")
        print("  --help      Show help message")
        print(f"\n{'=' * 60}\n")

        assistant = PhoneAssistant(config=config)
        assistant.start()

    return 0


if __name__ == "__main__":
    sys.exit(main())
