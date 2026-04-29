from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SMSService(ABC):
    """Abstract base class for SMS services"""

    @abstractmethod
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send SMS message

        Args:
            to: Recipient phone number
            message: SMS message content

        Returns:
            Dict containing:
            - 'success': bool
            - 'message_id': str (optional)
            - 'error': str (optional)
        """
        pass

    @abstractmethod
    def get_balance(self) -> Optional[float]:
        """Get remaining SMS balance"""
        pass


class TwilioSMSService(SMSService):
    """Twilio SMS service implementation"""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        try:
            from twilio.rest import Client
            self.client = Client(account_sid, auth_token)
            self.from_number = from_number
        except ImportError:
            logger.warning("Twilio package not installed")
            self.client = None

    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        if not self.client:
            return {
                'success': False,
                'error': 'Twilio package not installed'
            }

        try:
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            return {
                'success': True,
                'message_id': twilio_message.sid
            }
        except Exception as e:
            logger.error(f"Twilio SMS sending failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_balance(self) -> Optional[float]:
        # Twilio doesn't provide direct balance API
        # You'd need to check their dashboard or use webhooks
        return None


class MockSMSService(SMSService):
    """Mock SMS service for testing/development"""

    def __init__(self):
        self.sent_messages = []

    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        # Simulate SMS sending
        import time
        message_id = f"mock_{int(time.time())}_{len(self.sent_messages)}"

        self.sent_messages.append({
            'to': to,
            'message': message,
            'message_id': message_id,
            'timestamp': time.time()
        })

        logger.info(f"Mock SMS sent to {to}: {message[:50]}...")
        return {
            'success': True,
            'message_id': message_id
        }

    def get_balance(self) -> Optional[float]:
        return 1000.0  # Mock balance


class DisabledSMSService(SMSService):
    """Disabled SMS service - doesn't send actual SMS"""

    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        logger.info(f"SMS sending disabled. Would send to {to}: {message[:50]}...")
        return {
            'success': False,
            'error': 'SMS service is currently disabled'
        }

    def get_balance(self) -> Optional[float]:
        return None


def get_sms_service() -> SMSService:
    """Factory function to get SMS service based on settings"""
    from django.conf import settings

    service_type = getattr(settings, 'SMS_SERVICE_TYPE', 'disabled')

    if service_type == 'twilio':
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')

        if not all([account_sid, auth_token, from_number]):
            logger.warning("Twilio credentials not configured, falling back to disabled service")
            return DisabledSMSService()

        return TwilioSMSService(account_sid, auth_token, from_number)

    elif service_type == 'mock':
        return MockSMSService()

    else:  # 'disabled' or any other value
        return DisabledSMSService()