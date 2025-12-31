"""EasyAppointments integration for AI Phone Assistant (cal.aiqso.io)."""

import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.utils.logger import setup_logger


class EasyAppointmentsClient:
    """Client for EasyAppointments API at cal.aiqso.io."""

    def __init__(
        self,
        base_url: str = "https://cal.aiqso.io",
        api_token: str = None
    ):
        """
        Initialize EasyAppointments client.

        Args:
            base_url: EasyAppointments API URL
            api_token: API token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.logger = setup_logger(__name__)

        # Default service and provider IDs (configured for AIQSO)
        self.default_service_id = 1  # Consultation service
        self.default_provider_id = 1  # Primary provider

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make an API request."""
        try:
            url = f"{self.base_url}/index.php/api/v1{endpoint}"
            with httpx.Client(timeout=15.0) as client:
                if method == "GET":
                    response = client.get(url, headers=self._get_headers())
                elif method == "POST":
                    response = client.post(url, headers=self._get_headers(), json=data)
                elif method == "PUT":
                    response = client.put(url, headers=self._get_headers(), json=data)
                elif method == "DELETE":
                    response = client.delete(url, headers=self._get_headers())
                else:
                    return None

                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    self.logger.error(f"EasyAppointments API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            self.logger.error(f"EasyAppointments request failed: {e}")
            return None

    def get_services(self) -> List[Dict]:
        """Get available services."""
        result = self._request("GET", "/services")
        return result if isinstance(result, list) else []

    def get_providers(self) -> List[Dict]:
        """Get available service providers."""
        result = self._request("GET", "/providers")
        return result if isinstance(result, list) else []

    def get_availabilities(
        self,
        service_id: int = None,
        provider_id: int = None,
        date: str = None
    ) -> List[str]:
        """
        Get available time slots for a specific date.

        Args:
            service_id: Service ID (defaults to consultation)
            provider_id: Provider ID (defaults to primary)
            date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            List[str]: Available time slots
        """
        service_id = service_id or self.default_service_id
        provider_id = provider_id or self.default_provider_id
        date = date or datetime.now().strftime("%Y-%m-%d")

        result = self._request(
            "GET",
            f"/availabilities?providerId={provider_id}&serviceId={service_id}&date={date}"
        )

        return result if isinstance(result, list) else []

    def get_next_available_slots(self, days_ahead: int = 7) -> List[Dict]:
        """
        Get next available appointment slots.

        Args:
            days_ahead: Number of days to search ahead

        Returns:
            List[Dict]: Available slots with date and times
        """
        available_slots = []
        today = datetime.now()

        for i in range(days_ahead):
            check_date = today + timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")
            day_name = check_date.strftime("%A")

            times = self.get_availabilities(date=date_str)
            if times:
                available_slots.append({
                    "date": date_str,
                    "day": day_name,
                    "times": times[:5]  # Limit to first 5 slots
                })

            # Stop after finding 3 days with availability
            if len(available_slots) >= 3:
                break

        return available_slots

    def find_customer_by_phone(self, phone: str) -> Optional[Dict]:
        """
        Find a customer by phone number.

        Args:
            phone: Phone number to search

        Returns:
            Optional[Dict]: Customer data or None
        """
        # Normalize phone
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]

        result = self._request("GET", f"/customers?q={digits[-10:]}")

        if isinstance(result, list) and result:
            return result[0]
        return None

    def create_customer(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        notes: str = ""
    ) -> Optional[Dict]:
        """
        Create a new customer.

        Args:
            first_name: Customer's first name
            last_name: Customer's last name
            email: Customer's email
            phone: Customer's phone number
            notes: Optional notes

        Returns:
            Optional[Dict]: Created customer data
        """
        data = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "notes": notes
        }

        return self._request("POST", "/customers", data)

    def get_customer_appointments(self, customer_id: int) -> List[Dict]:
        """
        Get appointments for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            List[Dict]: Customer's appointments
        """
        # Get all appointments and filter
        result = self._request("GET", "/appointments")

        if isinstance(result, list):
            return [
                apt for apt in result
                if apt.get("customerId") == customer_id
            ]
        return []

    def create_appointment(
        self,
        customer_id: int,
        start_datetime: str,
        end_datetime: str,
        service_id: int = None,
        provider_id: int = None,
        notes: str = ""
    ) -> Optional[Dict]:
        """
        Create a new appointment.

        Args:
            customer_id: Customer ID
            start_datetime: Start time (YYYY-MM-DD HH:MM:SS)
            end_datetime: End time (YYYY-MM-DD HH:MM:SS)
            service_id: Service ID
            provider_id: Provider ID
            notes: Appointment notes

        Returns:
            Optional[Dict]: Created appointment data
        """
        data = {
            "start": start_datetime,
            "end": end_datetime,
            "serviceId": service_id or self.default_service_id,
            "providerId": provider_id or self.default_provider_id,
            "customerId": customer_id,
            "notes": notes
        }

        result = self._request("POST", "/appointments", data)

        if result:
            self.logger.info(f"Created appointment for customer {customer_id}")
        return result

    def book_appointment(
        self,
        phone: str,
        name: str,
        email: str,
        preferred_date: str = None,
        preferred_time: str = None,
        notes: str = ""
    ) -> Dict:
        """
        High-level method to book an appointment for a caller.

        Args:
            phone: Caller's phone number
            name: Caller's name
            email: Caller's email
            preferred_date: Preferred date (YYYY-MM-DD)
            preferred_time: Preferred time (HH:MM)
            notes: Appointment notes

        Returns:
            Dict: Booking result with status and details
        """
        # Find or create customer
        customer = self.find_customer_by_phone(phone)

        if not customer:
            # Split name into first/last
            name_parts = name.split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            customer = self.create_customer(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                notes=f"Created by AI Phone Assistant"
            )

            if not customer:
                return {
                    "success": False,
                    "message": "Unable to create customer record"
                }

        customer_id = customer.get("id")

        # Find available slot
        if preferred_date:
            available_times = self.get_availabilities(date=preferred_date)

            if not available_times:
                # Get next available
                next_slots = self.get_next_available_slots()
                if next_slots:
                    suggestion = next_slots[0]
                    return {
                        "success": False,
                        "message": f"No availability on {preferred_date}",
                        "suggestion": f"Next available is {suggestion['day']}, {suggestion['date']} at {suggestion['times'][0]}",
                        "available_slots": next_slots
                    }
                return {
                    "success": False,
                    "message": "No available appointments found"
                }

            # Use preferred time or first available
            if preferred_time and preferred_time in available_times:
                selected_time = preferred_time
            else:
                selected_time = available_times[0]

            start_datetime = f"{preferred_date} {selected_time}:00"
        else:
            # Get next available slot
            next_slots = self.get_next_available_slots()
            if not next_slots:
                return {
                    "success": False,
                    "message": "No available appointments found"
                }

            slot = next_slots[0]
            preferred_date = slot["date"]
            selected_time = slot["times"][0]
            start_datetime = f"{preferred_date} {selected_time}:00"

        # Calculate end time (default 30 min appointment)
        start_dt = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        end_dt = start_dt + timedelta(minutes=30)
        end_datetime = end_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Create appointment
        appointment = self.create_appointment(
            customer_id=customer_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            notes=notes or "Booked via AI Phone Assistant"
        )

        if appointment:
            return {
                "success": True,
                "message": f"Appointment booked for {start_dt.strftime('%A, %B %d at %I:%M %p')}",
                "appointment_id": appointment.get("id"),
                "date": preferred_date,
                "time": selected_time,
                "customer_id": customer_id
            }

        return {
            "success": False,
            "message": "Failed to create appointment"
        }

    def cancel_appointment(self, appointment_id: int) -> bool:
        """
        Cancel an appointment.

        Args:
            appointment_id: Appointment ID

        Returns:
            bool: True if cancelled successfully
        """
        result = self._request("DELETE", f"/appointments/{appointment_id}")
        return result is not None

    def reschedule_appointment(
        self,
        appointment_id: int,
        new_date: str,
        new_time: str
    ) -> Optional[Dict]:
        """
        Reschedule an existing appointment.

        Args:
            appointment_id: Appointment ID
            new_date: New date (YYYY-MM-DD)
            new_time: New time (HH:MM)

        Returns:
            Optional[Dict]: Updated appointment data
        """
        start_datetime = f"{new_date} {new_time}:00"
        start_dt = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        end_dt = start_dt + timedelta(minutes=30)
        end_datetime = end_dt.strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "start": start_datetime,
            "end": end_datetime
        }

        return self._request("PUT", f"/appointments/{appointment_id}", data)

    def get_appointment_summary(self, phone: str) -> str:
        """
        Get a natural language summary of upcoming appointments for a caller.

        Args:
            phone: Caller's phone number

        Returns:
            str: Natural language summary
        """
        customer = self.find_customer_by_phone(phone)

        if not customer:
            return "I don't have any appointments on file for this phone number."

        appointments = self.get_customer_appointments(customer["id"])

        if not appointments:
            return f"Hi {customer.get('firstName', 'there')}! I don't see any upcoming appointments for you."

        # Filter to future appointments
        now = datetime.now()
        upcoming = [
            apt for apt in appointments
            if datetime.strptime(apt["start"], "%Y-%m-%d %H:%M:%S") > now
        ]

        if not upcoming:
            return f"Hi {customer.get('firstName', 'there')}! You don't have any upcoming appointments."

        # Format the next appointment
        next_apt = sorted(upcoming, key=lambda x: x["start"])[0]
        apt_time = datetime.strptime(next_apt["start"], "%Y-%m-%d %H:%M:%S")

        return (
            f"Hi {customer.get('firstName', 'there')}! "
            f"Your next appointment is on {apt_time.strftime('%A, %B %d at %I:%M %p')}."
        )
