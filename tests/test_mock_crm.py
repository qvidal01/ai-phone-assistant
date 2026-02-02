"""Tests for MockCRM implementation."""

from datetime import datetime, timedelta

import pytest

from src.integrations.mock_crm import MockCRM


@pytest.fixture
def crm():
    """Create a MockCRM instance for testing."""
    return MockCRM()


@pytest.fixture
def sample_customer(crm):
    """Create a sample customer."""
    return crm.create_customer(
        {"name": "John Doe", "email": "john@example.com", "phone": "+1234567890"}
    )


def test_create_customer(crm):
    """Test creating a customer."""
    customer_data = {"name": "Jane Smith", "email": "jane@example.com", "phone": "+9876543210"}

    customer = crm.create_customer(customer_data)

    assert customer["name"] == "Jane Smith"
    assert customer["email"] == "jane@example.com"
    assert customer["phone"] == "+9876543210"
    assert "id" in customer


def test_get_customer_by_phone(crm, sample_customer):
    """Test retrieving customer by phone number."""
    customer = crm.get_customer("+1234567890")

    assert customer is not None
    assert customer["name"] == "John Doe"
    assert customer["email"] == "john@example.com"


def test_get_customer_not_found(crm):
    """Test retrieving non-existent customer."""
    customer = crm.get_customer("+0000000000")
    assert customer is None


def test_update_customer(crm, sample_customer):
    """Test updating customer information."""
    updated = crm.update_customer(sample_customer["id"], {"email": "newemail@example.com"})

    assert updated["email"] == "newemail@example.com"
    assert updated["name"] == "John Doe"  # Unchanged


def test_create_note(crm, sample_customer):
    """Test creating a customer note."""
    note = crm.create_note(sample_customer["id"], "Customer called about appointment")

    assert note["content"] == "Customer called about appointment"
    assert note["customer_id"] == sample_customer["id"]
    assert "created_at" in note


def test_create_appointment(crm, sample_customer):
    """Test creating an appointment."""
    appointment_time = datetime.now() + timedelta(days=1)

    appointment = crm.create_appointment(
        {
            "customer_id": sample_customer["id"],
            "scheduled_time": appointment_time.isoformat(),
            "service": "Consultation",
        }
    )

    assert appointment["customer_id"] == sample_customer["id"]
    assert appointment["service"] == "Consultation"
    assert appointment["status"] == "scheduled"
    assert "id" in appointment


def test_get_appointments(crm, sample_customer):
    """Test retrieving customer appointments."""
    # Create multiple appointments
    tomorrow = datetime.now() + timedelta(days=1)
    next_week = datetime.now() + timedelta(days=7)

    crm.create_appointment(
        {
            "customer_id": sample_customer["id"],
            "scheduled_time": tomorrow.isoformat(),
            "service": "Service A",
        }
    )

    crm.create_appointment(
        {
            "customer_id": sample_customer["id"],
            "scheduled_time": next_week.isoformat(),
            "service": "Service B",
        }
    )

    # Get all appointments
    appointments = crm.get_appointments(sample_customer["id"])
    assert len(appointments) == 2


def test_update_appointment(crm, sample_customer):
    """Test updating an appointment."""
    appointment = crm.create_appointment(
        {
            "customer_id": sample_customer["id"],
            "scheduled_time": datetime.now().isoformat(),
            "service": "Original Service",
        }
    )

    updated = crm.update_appointment(appointment["id"], {"service": "Updated Service"})

    assert updated["service"] == "Updated Service"


def test_cancel_appointment(crm, sample_customer):
    """Test canceling an appointment."""
    appointment = crm.create_appointment(
        {
            "customer_id": sample_customer["id"],
            "scheduled_time": datetime.now().isoformat(),
            "service": "Test Service",
        }
    )

    result = crm.cancel_appointment(appointment["id"])
    assert result is True

    # Verify appointment is cancelled
    appointments = crm.get_appointments(sample_customer["id"])
    assert appointments[0]["status"] == "cancelled"
