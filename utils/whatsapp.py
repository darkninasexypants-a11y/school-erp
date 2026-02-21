import os
from typing import Tuple

def _get_twilio_client():
    try:
        from twilio.rest import Client
    except Exception:
        return None
    sid = os.environ.get("TWILIO_ACCOUNT_SID") or ""
    token = os.environ.get("TWILIO_AUTH_TOKEN") or ""
    if not sid or not token:
        return None
    return Client(sid, token)

def send_whatsapp_message(to_phone: str, body: str) -> Tuple[bool, str]:
    """
    Send a WhatsApp message via Twilio if credentials are available.
    Returns (success, info/message)
    """
    client = _get_twilio_client()
    if client is None:
        return False, "Twilio client not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
    from_number = os.environ.get("TWILIO_WHATSAPP_NUMBER") or "whatsapp:+14155238886"
    to_number = f"whatsapp:{to_phone}"
    try:
        client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        return True, "Message sent"
    except Exception as exc:
        return False, str(exc)


