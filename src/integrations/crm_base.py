"""Base interface for CRM integrations."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class CRMBase(ABC):
    """Abstract base class for CRM integrations."""

    @abstractmethod
    def get_customer(self, phone_number: str) -> Optional[dict]:
        """
        Get customer information by phone number.

        Args:
            phone_number: Customer's phone number

        Returns:
            Optional[Dict]: Customer data or None if not found
        """
        pass

    @abstractmethod
    def create_customer(self, customer_data: dict) -> dict:
        """
        Create a new customer record.

        Args:
            customer_data: Customer information

        Returns:
            Dict: Created customer data with ID
        """
        pass

    @abstractmethod
    def update_customer(self, customer_id: str, customer_data: dict) -> dict:
        """
        Update an existing customer record.

        Args:
            customer_id: Customer ID
            customer_data: Updated customer information

        Returns:
            Dict: Updated customer data
        """
        pass

    @abstractmethod
    def create_note(self, customer_id: str, note: str) -> dict:
        """
        Add a note to a customer record.

        Args:
            customer_id: Customer ID
            note: Note content

        Returns:
            Dict: Created note data
        """
        pass

    @abstractmethod
    def get_appointments(
        self,
        customer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        """
        Get customer appointments.

        Args:
            customer_id: Customer ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List[Dict]: List of appointments
        """
        pass

    @abstractmethod
    def create_appointment(self, appointment_data: dict) -> dict:
        """
        Create a new appointment.

        Args:
            appointment_data: Appointment information

        Returns:
            Dict: Created appointment data
        """
        pass

    @abstractmethod
    def update_appointment(self, appointment_id: str, appointment_data: dict) -> dict:
        """
        Update an existing appointment.

        Args:
            appointment_id: Appointment ID
            appointment_data: Updated appointment information

        Returns:
            Dict: Updated appointment data
        """
        pass

    @abstractmethod
    def cancel_appointment(self, appointment_id: str) -> bool:
        """
        Cancel an appointment.

        Args:
            appointment_id: Appointment ID

        Returns:
            bool: True if successful
        """
        pass
