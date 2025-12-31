"""Odoo CRM integration for AI Phone Assistant."""

import httpx
from typing import Dict, List, Optional
from datetime import datetime
from src.integrations.crm_base import CRMBase
from src.utils.logger import setup_logger


class OdooCRM(CRMBase):
    """Odoo CRM integration for customer and call management."""

    def __init__(
        self,
        url: str = "http://192.168.0.230:8069",
        database: str = "aiqso_db",
        username: str = "quinn@aiqso.io",
        password: str = None
    ):
        """
        Initialize Odoo CRM client.

        Args:
            url: Odoo server URL
            database: Odoo database name
            username: Odoo username
            password: Odoo API password/key
        """
        self.url = url.rstrip("/")
        self.database = database
        self.username = username
        self.password = password
        self.uid = None
        self.logger = setup_logger(__name__)

        # Cache for phone number to partner ID mapping
        self._phone_cache: Dict[str, int] = {}

    def _authenticate(self) -> Optional[int]:
        """Authenticate with Odoo and get user ID."""
        if self.uid:
            return self.uid

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.url}/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "call",
                        "params": {
                            "service": "common",
                            "method": "authenticate",
                            "args": [
                                self.database,
                                self.username,
                                self.password,
                                {}
                            ]
                        },
                        "id": 1
                    }
                )
                result = response.json()
                self.uid = result.get("result")
                if self.uid:
                    self.logger.info(f"Authenticated with Odoo as uid={self.uid}")
                return self.uid
        except Exception as e:
            self.logger.error(f"Odoo authentication failed: {e}")
            return None

    def _call(self, model: str, method: str, args: list, kwargs: dict = None) -> any:
        """Make a JSON-RPC call to Odoo."""
        if not self._authenticate():
            return None

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{self.url}/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "call",
                        "params": {
                            "service": "object",
                            "method": "execute_kw",
                            "args": [
                                self.database,
                                self.uid,
                                self.password,
                                model,
                                method,
                                args,
                                kwargs or {}
                            ]
                        },
                        "id": 2
                    }
                )
                result = response.json()
                if "error" in result:
                    self.logger.error(f"Odoo error: {result['error']}")
                    return None
                return result.get("result")
        except Exception as e:
            self.logger.error(f"Odoo call failed: {e}")
            return None

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison."""
        # Remove all non-digits
        digits = ''.join(c for c in phone if c.isdigit())
        # Handle US numbers - remove leading 1
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]
        return digits

    def get_customer(self, phone_number: str) -> Optional[Dict]:
        """
        Get customer information by phone number.

        Args:
            phone_number: Customer's phone number

        Returns:
            Optional[Dict]: Customer data or None if not found
        """
        normalized = self._normalize_phone(phone_number)

        # Check cache first
        if normalized in self._phone_cache:
            partner_id = self._phone_cache[normalized]
            partners = self._call(
                "res.partner",
                "read",
                [[partner_id]],
                {"fields": ["id", "name", "phone", "mobile", "email", "comment"]}
            )
            if partners:
                p = partners[0]
                return {
                    "id": p["id"],
                    "name": p["name"],
                    "phone": p.get("phone") or p.get("mobile"),
                    "email": p.get("email"),
                    "notes": p.get("comment", "")
                }

        # Search by phone or mobile
        partner_ids = self._call(
            "res.partner",
            "search",
            [["|", ("phone", "ilike", normalized[-10:]), ("mobile", "ilike", normalized[-10:])]],
            {"limit": 1}
        )

        if not partner_ids:
            self.logger.info(f"No customer found for phone: {phone_number}")
            return None

        # Cache the result
        self._phone_cache[normalized] = partner_ids[0]

        partners = self._call(
            "res.partner",
            "read",
            [partner_ids],
            {"fields": ["id", "name", "phone", "mobile", "email", "comment"]}
        )

        if partners:
            p = partners[0]
            self.logger.info(f"Found customer: {p['name']}")
            return {
                "id": p["id"],
                "name": p["name"],
                "phone": p.get("phone") or p.get("mobile"),
                "email": p.get("email"),
                "notes": p.get("comment", "")
            }

        return None

    def create_customer(self, customer_data: Dict) -> Dict:
        """
        Create a new customer record in Odoo.

        Args:
            customer_data: Customer information

        Returns:
            Dict: Created customer data with ID
        """
        partner_vals = {
            "name": customer_data.get("name", "Unknown Caller"),
            "phone": customer_data.get("phone"),
            "email": customer_data.get("email"),
            "comment": customer_data.get("notes", "Created by AI Phone Assistant"),
            "is_company": False,
        }

        partner_id = self._call("res.partner", "create", [partner_vals])

        if partner_id:
            self.logger.info(f"Created customer in Odoo: {partner_id}")
            # Cache the phone
            if customer_data.get("phone"):
                normalized = self._normalize_phone(customer_data["phone"])
                self._phone_cache[normalized] = partner_id

            return {
                "id": partner_id,
                **customer_data
            }

        return customer_data

    def update_customer(self, customer_id: str, customer_data: Dict) -> Dict:
        """Update an existing customer record."""
        partner_vals = {}
        if "name" in customer_data:
            partner_vals["name"] = customer_data["name"]
        if "phone" in customer_data:
            partner_vals["phone"] = customer_data["phone"]
        if "email" in customer_data:
            partner_vals["email"] = customer_data["email"]
        if "notes" in customer_data:
            partner_vals["comment"] = customer_data["notes"]

        if partner_vals:
            self._call("res.partner", "write", [[int(customer_id)], partner_vals])

        return {"id": customer_id, **customer_data}

    def create_note(self, customer_id: str, note: str) -> Dict:
        """
        Add a note to a customer record (creates a CRM lead/activity).

        Args:
            customer_id: Customer ID
            note: Note content

        Returns:
            Dict: Created note data
        """
        # Create a mail.message (chatter note) on the partner
        message_vals = {
            "body": note,
            "model": "res.partner",
            "res_id": int(customer_id),
            "message_type": "comment",
            "subtype_id": 2,  # Note subtype
        }

        message_id = self._call("mail.message", "create", [message_vals])

        if message_id:
            self.logger.info(f"Created note on partner {customer_id}: {message_id}")
            return {"id": message_id, "note": note, "customer_id": customer_id}

        # Fallback: Update comment field
        existing = self._call(
            "res.partner",
            "read",
            [[int(customer_id)]],
            {"fields": ["comment"]}
        )

        if existing:
            current_comment = existing[0].get("comment") or ""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_comment = f"{current_comment}\n\n[{timestamp}] {note}"
            self._call("res.partner", "write", [[int(customer_id)], {"comment": new_comment}])

        return {"note": note, "customer_id": customer_id}

    def create_lead(self, phone_number: str, subject: str, description: str) -> Optional[Dict]:
        """
        Create a CRM lead from a phone call.

        Args:
            phone_number: Caller's phone number
            subject: Lead subject/name
            description: Lead description/notes

        Returns:
            Optional[Dict]: Created lead data
        """
        lead_vals = {
            "name": subject,
            "description": description,
            "phone": phone_number,
            "type": "lead",
        }

        # Link to existing partner if found
        customer = self.get_customer(phone_number)
        if customer:
            lead_vals["partner_id"] = customer["id"]
            lead_vals["contact_name"] = customer["name"]
            lead_vals["email_from"] = customer.get("email")

        lead_id = self._call("crm.lead", "create", [lead_vals])

        if lead_id:
            self.logger.info(f"Created CRM lead: {lead_id}")
            return {"id": lead_id, "name": subject, "phone": phone_number}

        return None

    def get_appointments(
        self,
        customer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get customer appointments (calendar events)."""
        domain = [("partner_ids", "in", [int(customer_id)])]

        if start_date:
            domain.append(("start", ">=", start_date.isoformat()))
        if end_date:
            domain.append(("stop", "<=", end_date.isoformat()))

        event_ids = self._call("calendar.event", "search", [domain], {"limit": 20})

        if not event_ids:
            return []

        events = self._call(
            "calendar.event",
            "read",
            [event_ids],
            {"fields": ["id", "name", "start", "stop", "description", "location"]}
        )

        return [
            {
                "id": e["id"],
                "title": e["name"],
                "start": e["start"],
                "end": e["stop"],
                "description": e.get("description", ""),
                "location": e.get("location", "")
            }
            for e in (events or [])
        ]

    def create_appointment(self, appointment_data: Dict) -> Dict:
        """Create a new appointment (calendar event)."""
        event_vals = {
            "name": appointment_data.get("title", "Phone Appointment"),
            "start": appointment_data["start"],
            "stop": appointment_data["end"],
            "description": appointment_data.get("description", ""),
            "location": appointment_data.get("location", ""),
        }

        if "customer_id" in appointment_data:
            event_vals["partner_ids"] = [(4, int(appointment_data["customer_id"]))]

        event_id = self._call("calendar.event", "create", [event_vals])

        if event_id:
            self.logger.info(f"Created calendar event: {event_id}")
            return {"id": event_id, **appointment_data}

        return appointment_data

    def update_appointment(self, appointment_id: str, appointment_data: Dict) -> Dict:
        """Update an existing appointment."""
        event_vals = {}
        if "title" in appointment_data:
            event_vals["name"] = appointment_data["title"]
        if "start" in appointment_data:
            event_vals["start"] = appointment_data["start"]
        if "end" in appointment_data:
            event_vals["stop"] = appointment_data["end"]
        if "description" in appointment_data:
            event_vals["description"] = appointment_data["description"]

        if event_vals:
            self._call("calendar.event", "write", [[int(appointment_id)], event_vals])

        return {"id": appointment_id, **appointment_data}

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment (delete the event)."""
        result = self._call("calendar.event", "unlink", [[int(appointment_id)]])
        return result is not None

    def log_call(self, phone_number: str, summary: str, duration: int = 0) -> Optional[Dict]:
        """
        Log a phone call in Odoo.

        Args:
            phone_number: Caller's phone number
            summary: Call summary
            duration: Call duration in seconds

        Returns:
            Optional[Dict]: Created activity data
        """
        customer = self.get_customer(phone_number)

        # Create a phone call activity
        activity_vals = {
            "res_model": "res.partner",
            "res_id": customer["id"] if customer else None,
            "activity_type_id": 2,  # Phone Call activity type
            "summary": f"AI Phone Call: {summary[:100]}",
            "note": summary,
        }

        if customer:
            activity_vals["res_id"] = customer["id"]
            activity_id = self._call("mail.activity", "create", [activity_vals])
            if activity_id:
                # Mark as done
                self._call("mail.activity", "action_done", [[activity_id]])
                self.logger.info(f"Logged call for customer {customer['name']}")
                return {"id": activity_id, "customer_id": customer["id"]}

        # If no customer, create a lead
        lead = self.create_lead(
            phone_number=phone_number,
            subject=f"AI Phone Call - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=summary
        )

        return lead
