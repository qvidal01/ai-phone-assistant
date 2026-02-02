"""Example showing how to run the Phone Assistant server."""

import os
import sys

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uvicorn

from src.server import app


def main():
    """
    Run the Phone Assistant server.

    This starts a FastAPI server that:
    - Handles incoming calls at /voice/incoming
    - Processes speech input at /voice/process
    - Handles call status callbacks at /voice/status
    - Processes incoming SMS at /sms/incoming

    Configure your Twilio webhooks to point to:
    - Voice: https://your-domain.com/voice/incoming
    - SMS: https://your-domain.com/sms/incoming
    - Status Callback: https://your-domain.com/voice/status
    """

    print("=" * 60)
    print("AI Phone Assistant Server")
    print("=" * 60)
    print("\nStarting server on http://0.0.0.0:8000")
    print("\nWebhook Endpoints:")
    print("  - Incoming Calls: POST /voice/incoming")
    print("  - Voice Processing: POST /voice/process")
    print("  - Call Status: POST /voice/status")
    print("  - Incoming SMS: POST /sms/incoming")
    print("\nHealth Check:")
    print("  - GET /")
    print("\n" + "=" * 60)
    print("\nPress Ctrl+C to stop the server")
    print()

    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
