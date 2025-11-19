"""Mock CRM implementation for testing and development."""

from typing import Dict, List, Optional
from datetime import datetime
from src.integrations.crm_base import CRMBase
from src.utils.logger import setup_logger


class MockCRM(CRMBase):
    """Mock CRM implementation using in-memory storage."""

    def __init__(self):
        """Initialize mock CRM with sample data."""
        self.logger = setup_logger(__name__)
        self.customers: Dict[str, Dict] = {}
        self.appointments: Dict[str, Dict] = {}
        self.notes: Dict[str, List[Dict]] = {}
        self._customer_id_counter = 1
        self._appointment_id_counter = 1
        self._note_id_counter = 1

    def get_customer(self, phone_number: str) -> Optional[Dict]:
        """Get customer by phone number."""
        for customer_id, customer in self.customers.items():
            if customer.get("phone") == phone_number:
                self.logger.info(f"Found customer: {customer_id}")
                return {**customer, "id": customer_id}
        self.logger.info(f"No customer found for phone: {phone_number}")
        return None

    def create_customer(self, customer_data: Dict) -> Dict:
        """Create a new customer."""
        customer_id = f"cust_{self._customer_id_counter}"
        self._customer_id_counter += 1

        self.customers[customer_id] = customer_data
        self.notes[customer_id] = []

        self.logger.info(f"Created customer: {customer_id}")
        return {**customer_data, "id": customer_id}

    def update_customer(self, customer_id: str, customer_data: Dict) -> Dict:
        """Update customer information."""
        if customer_id not in self.customers:
            raise ValueError(f"Customer {customer_id} not found")

        self.customers[customer_id].update(customer_data)
        self.logger.info(f"Updated customer: {customer_id}")
        return {**self.customers[customer_id], "id": customer_id}

    def create_note(self, customer_id: str, note: str) -> Dict:
        """Add a note to customer record."""
        if customer_id not in self.customers:
            raise ValueError(f"Customer {customer_id} not found")

        note_id = f"note_{self._note_id_counter}"
        self._note_id_counter += 1

        note_data = {
            "id": note_id,
            "customer_id": customer_id,
            "content": note,
            "created_at": datetime.now().isoformat()
        }

        if customer_id not in self.notes:
            self.notes[customer_id] = []

        self.notes[customer_id].append(note_data)
        self.logger.info(f"Created note: {note_id} for customer: {customer_id}")
        return note_data

    def get_appointments(
        self,
        customer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get customer appointments."""
        customer_appointments = [
            appt for appt in self.appointments.values()
            if appt.get("customer_id") == customer_id
        ]

        # Filter by date range if provided
        if start_date:
            customer_appointments = [
                appt for appt in customer_appointments
                if datetime.fromisoformat(appt["scheduled_time"]) >= start_date
            ]

        if end_date:
            customer_appointments = [
                appt for appt in customer_appointments
                if datetime.fromisoformat(appt["scheduled_time"]) <= end_date
            ]

        self.logger.info(f"Found {len(customer_appointments)} appointments for {customer_id}")
        return customer_appointments

    def create_appointment(self, appointment_data: Dict) -> Dict:
        """Create a new appointment."""
        appointment_id = f"appt_{self._appointment_id_counter}"
        self._appointment_id_counter += 1

        appointment = {
            **appointment_data,
            "id": appointment_id,
            "created_at": datetime.now().isoformat(),
            "status": "scheduled"
        }

        self.appointments[appointment_id] = appointment
        self.logger.info(f"Created appointment: {appointment_id}")
        return appointment

    def update_appointment(self, appointment_id: str, appointment_data: Dict) -> Dict:
        """Update an existing appointment."""
        if appointment_id not in self.appointments:
            raise ValueError(f"Appointment {appointment_id} not found")

        self.appointments[appointment_id].update(appointment_data)
        self.logger.info(f"Updated appointment: {appointment_id}")
        return self.appointments[appointment_id]

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        if appointment_id not in self.appointments:
            raise ValueError(f"Appointment {appointment_id} not found")

        self.appointments[appointment_id]["status"] = "cancelled"
        self.appointments[appointment_id]["cancelled_at"] = datetime.now().isoformat()
        self.logger.info(f"Cancelled appointment: {appointment_id}")
        return True
