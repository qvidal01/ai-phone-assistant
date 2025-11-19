"""Example demonstrating CRM integration."""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.integrations.mock_crm import MockCRM


def main():
    """
    Demonstrate CRM integration features.

    This example shows how to:
    1. Create and manage customer records
    2. Schedule and manage appointments
    3. Add notes to customer records
    """

    print("AI Phone Assistant - CRM Integration Example")
    print("=" * 60)

    # Initialize CRM (using MockCRM for demonstration)
    print("\n1. Initializing CRM...")
    crm = MockCRM()
    print("   ✓ CRM initialized (using MockCRM)")

    # Create a customer
    print("\n2. Creating a new customer...")
    customer = crm.create_customer({
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "+1555123456",
        "address": "123 Main St, Anytown, USA"
    })
    print(f"   ✓ Customer created: {customer['name']} (ID: {customer['id']})")

    # Retrieve customer by phone number
    print("\n3. Looking up customer by phone number...")
    found_customer = crm.get_customer("+1555123456")
    if found_customer:
        print(f"   ✓ Found: {found_customer['name']}")
    else:
        print("   ✗ Customer not found")

    # Create an appointment
    print("\n4. Scheduling an appointment...")
    appointment_time = datetime.now() + timedelta(days=3)
    appointment = crm.create_appointment({
        "customer_id": customer['id'],
        "scheduled_time": appointment_time.isoformat(),
        "service": "Car Maintenance",
        "notes": "Oil change and tire rotation"
    })
    print(f"   ✓ Appointment scheduled for {appointment_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Service: {appointment['service']}")
    print(f"   Status: {appointment['status']}")

    # Add a note to customer record
    print("\n5. Adding note to customer record...")
    note = crm.create_note(
        customer['id'],
        "Customer called to confirm appointment. Very friendly."
    )
    print(f"   ✓ Note added: {note['content'][:50]}...")

    # Get all customer appointments
    print("\n6. Retrieving customer appointments...")
    appointments = crm.get_appointments(customer['id'])
    print(f"   ✓ Found {len(appointments)} appointment(s)")
    for appt in appointments:
        print(f"      - {appt['service']} on {appt['scheduled_time'][:10]}")

    # Update appointment
    print("\n7. Updating appointment...")
    updated_appt = crm.update_appointment(
        appointment['id'],
        {"notes": "Oil change, tire rotation, and brake inspection"}
    )
    print(f"   ✓ Appointment updated")
    print(f"   New notes: {updated_appt['notes']}")

    # Update customer information
    print("\n8. Updating customer information...")
    updated_customer = crm.update_customer(
        customer['id'],
        {"email": "alice.johnson@newdomain.com"}
    )
    print(f"   ✓ Customer email updated to: {updated_customer['email']}")

    # Cancel appointment
    print("\n9. Canceling appointment...")
    crm.cancel_appointment(appointment['id'])
    print(f"   ✓ Appointment cancelled")

    # Verify cancellation
    cancelled_appts = crm.get_appointments(customer['id'])
    print(f"   Status: {cancelled_appts[0]['status']}")

    print("\n" + "=" * 60)
    print("CRM Integration Example completed!")
    print("\nNote: This example uses MockCRM (in-memory storage).")
    print("In production, implement CRMBase for your actual CRM system.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
