"""
WhatsApp notifications.

No WhatsApp Business API key is configured yet, so instead of sending
messages automatically we generate a "click to send" wa.me deep link
pre-filled with the message. Staff/admin click it from the dashboard to
open WhatsApp Web/App and hit send themselves.

The company's WhatsApp number is configured in settings.WHATSAPP_BUSINESS_NUMBER
(currently 923145355656, i.e. wa.me/923145355656).

Swap-in path for later: once a WhatsApp Business API / Cloud API key is
available, replace `build_customer_whatsapp_link`'s caller with an actual
POST to the Graph API inside `send_whatsapp_message_via_api`, and endpoints
will not need to change (they already log through NotificationLog).
"""
from urllib.parse import quote
from typing import Optional

from app.core.config import settings


def build_customer_whatsapp_link(customer_phone: str, message: str) -> str:
    """Build a wa.me link to message a CUSTOMER (opened by staff/admin)."""
    digits = "".join(ch for ch in customer_phone if ch.isdigit())
    return f"https://wa.me/{digits}?text={quote(message)}"


def build_business_whatsapp_link(message: str) -> str:
    """Build a wa.me link to message the GOLD Px business number directly."""
    return f"https://wa.me/{settings.WHATSAPP_BUSINESS_NUMBER}?text={quote(message)}"


def send_whatsapp_message_via_api(to_phone: str, message: str) -> bool:
    """
    Placeholder for when a real WhatsApp Business/Cloud API key exists.
    Currently unused - raises to make it obvious this isn't wired up yet.
    """
    raise NotImplementedError(
        "No WhatsApp Business API credentials configured. "
        "Using build_customer_whatsapp_link() deep links instead."
    )
