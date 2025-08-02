"""
Mock email services for testing
Provides realistic email responses without sending real emails
"""

from typing import List, Dict, Optional
from flask_mail import Message


class MockMail:
    """Mock Flask-Mail instance"""

    def __init__(self):
        self.sent_messages = []
        self.send_count = 0
        self.should_fail = False
        self.fail_message = "Mock email sending failed"

    def send(self, message: Message) -> bool:
        """Mock email sending"""
        self.send_count += 1

        if self.should_fail:
            raise Exception(self.fail_message)

        # Store sent message details
        sent_message = {
            "id": f"mock-email-{self.send_count}",
            "subject": message.subject,
            "recipients": message.recipients,
            "sender": message.sender,
            "body": message.body,
            "html": message.html,
            "cc": getattr(message, "cc", []),
            "bcc": getattr(message, "bcc", []),
            "timestamp": f"2025-01-29T10:{self.send_count:02d}:00Z",
        }

        self.sent_messages.append(sent_message)
        return True

    def get_sent_messages(self) -> List[Dict]:
        """Get all sent messages"""
        return self.sent_messages

    def get_last_message(self) -> Optional[Dict]:
        """Get the last sent message"""
        return self.sent_messages[-1] if self.sent_messages else None

    def clear_sent_messages(self):
        """Clear sent messages history"""
        self.sent_messages = []
        self.send_count = 0

    def set_failure_mode(self, should_fail: bool = True, message: str = "Mock email failure"):
        """Set mock to fail email sending"""
        self.should_fail = should_fail
        self.fail_message = message


class MockMessage:
    """Mock Flask-Mail Message class"""

    def __init__(
        self,
        subject: str,
        recipients: List[str],
        body: str = "",
        html: str = "",
        sender: str = "test@example.com",
    ):
        self.subject = subject
        self.recipients = recipients if isinstance(recipients, list) else [recipients]
        self.body = body
        self.html = html
        self.sender = sender
        self.cc = []
        self.bcc = []
        self.attachments = []

    def attach(self, filename: str, content_type: str, data: bytes):
        """Mock attachment functionality"""
        self.attachments.append({"filename": filename, "content_type": content_type, "data": data})


class MockEmailService:
    """Mock email service that handles common email operations"""

    def __init__(self):
        self.mail = MockMail()
        self.templates = {
            "user_approved": {
                "subject": "Vaš račun je bil odobren - PD Triglav",
                "body": "Pozdravljeni {name},\n\nVaš račun je bil odobren.",
            },
            "user_rejected": {
                "subject": "Vaš račun ni bil odobren - PD Triglav",
                "body": "Pozdravljeni {name},\n\nŽal vašega računa nismo mogli odobriti.",
            },
            "trip_notification": {
                "subject": "Nova gorska tura - {trip_title}",
                "body": "Nova tura je na voljo: {trip_title}\nDatum: {trip_date}",
            },
            "password_reset": {
                "subject": "Ponastavitev gesla - PD Triglav",
                "body": "Kliknite na povezavo za ponastavitev: {reset_link}",
            },
        }

    def send_user_approval_email(self, user_email: str, user_name: str) -> bool:
        """Send user approval email"""
        template = self.templates["user_approved"]
        message = MockMessage(
            subject=template["subject"],
            recipients=[user_email],
            body=template["body"].format(name=user_name),
        )
        return self.mail.send(message)

    def send_user_rejection_email(self, user_email: str, user_name: str, reason: str = "") -> bool:
        """Send user rejection email"""
        template = self.templates["user_rejected"]
        body = template["body"].format(name=user_name)
        if reason:
            body += f"\n\nRazlog: {reason}"

        message = MockMessage(subject=template["subject"], recipients=[user_email], body=body)
        return self.mail.send(message)

    def send_trip_notification(
        self, recipients: List[str], trip_title: str, trip_date: str
    ) -> bool:
        """Send trip notification email"""
        template = self.templates["trip_notification"]
        message = MockMessage(
            subject=template["subject"].format(trip_title=trip_title),
            recipients=recipients,
            body=template["body"].format(trip_title=trip_title, trip_date=trip_date),
        )
        return self.mail.send(message)

    def send_password_reset_email(self, user_email: str, reset_link: str) -> bool:
        """Send password reset email"""
        template = self.templates["password_reset"]
        message = MockMessage(
            subject=template["subject"],
            recipients=[user_email],
            body=template["body"].format(reset_link=reset_link),
        )
        return self.mail.send(message)

    def send_bulk_email(self, recipients: List[str], subject: str, body: str) -> Dict:
        """Send bulk email to multiple recipients"""
        results = []
        for recipient in recipients:
            try:
                message = MockMessage(subject=subject, recipients=[recipient], body=body)
                success = self.mail.send(message)
                results.append({"email": recipient, "success": success})
            except Exception as e:
                results.append({"email": recipient, "success": False, "error": str(e)})

        return {
            "total_sent": len([r for r in results if r["success"]]),
            "total_failed": len([r for r in results if not r["success"]]),
            "results": results,
        }


def create_mock_mail():
    """Create a mock Flask-Mail instance"""
    return MockMail()


def create_mock_email_service():
    """Create a mock email service"""
    return MockEmailService()


# Patch helpers for email testing
def patch_email_services():
    """Returns patches for email service components"""
    return [
        ("flask_mail.Mail", MockMail),
        ("flask_mail.Message", MockMessage),
    ]


def patch_flask_mail():
    """Returns patch for Flask-Mail"""
    mock_mail = MockMail()
    return (
        "flask_mail",
        type("MockFlaskMail", (), {"Mail": lambda app=None: mock_mail, "Message": MockMessage})(),
    )


# Common email test scenarios
MOCK_EMAIL_SCENARIOS = {
    "user_approval": {
        "subject": "Vaš račun je bil odobren - PD Triglav",
        "recipients": ["user@example.com"],
        "body_contains": ["odobren", "račun"],
    },
    "trip_notification": {
        "subject": "Nova gorska tura - Test Trip",
        "recipients": ["member1@example.com", "member2@example.com"],
        "body_contains": ["nova tura", "Test Trip"],
    },
    "password_reset": {
        "subject": "Ponastavitev gesla - PD Triglav",
        "recipients": ["user@example.com"],
        "body_contains": ["ponastavitev", "povezavo"],
    },
    "bulk_notification": {
        "subject": "Obvestilo za vse člane",
        "recipients": ["member1@example.com", "member2@example.com", "member3@example.com"],
        "expected_success": 3,
        "expected_failed": 0,
    },
}
