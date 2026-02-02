"""Basic usage example for AI Phone Assistant."""

import os
import sys

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.assistant.phone_assistant import PhoneAssistant
from src.utils.config import load_config


def main():
    """
    Basic example showing how to initialize and use the Phone Assistant.

    This example demonstrates:
    1. Loading configuration from .env file
    2. Initializing the PhoneAssistant
    3. Making an outbound call
    4. Sending an SMS notification
    """

    print("AI Phone Assistant - Basic Usage Example")
    print("=" * 50)

    try:
        # Load configuration from environment
        print("\n1. Loading configuration...")
        config = load_config()
        print("   ✓ Configuration loaded")
        print(f"   Phone Number: {config.twilio_phone_number}")

        # Initialize Phone Assistant
        print("\n2. Initializing Phone Assistant...")
        PhoneAssistant(config=config)
        print("   ✓ Phone Assistant initialized")

        # Example: Make an outbound call
        print("\n3. Example: Making an outbound call")
        print("   (Commented out - uncomment to actually make a call)")
        # call_sid = assistant.make_outbound_call(
        #     to_number="+1234567890",
        #     message="Hello! This is a test call from the AI Phone Assistant."
        # )
        # print(f"   ✓ Call initiated: {call_sid}")

        # Example: Send an SMS notification
        print("\n4. Example: Sending an SMS notification")
        print("   (Commented out - uncomment to actually send SMS)")
        # message_sid = assistant.send_sms_notification(
        #     to_number="+1234567890",
        #     message="Hello! This is a test message from the AI Phone Assistant."
        # )
        # print(f"   ✓ SMS sent: {message_sid}")

        print("\n" + "=" * 50)
        print("Example completed successfully!")
        print("\nTo actually make calls or send SMS:")
        print("1. Set up your .env file with valid Twilio credentials")
        print("2. Uncomment the example code above")
        print("3. Replace the phone numbers with valid numbers")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file with your API keys")
        print("2. Installed all dependencies (pip install -r requirements.txt)")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
