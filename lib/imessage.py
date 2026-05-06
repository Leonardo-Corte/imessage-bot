"""iMessage availability check + handle normalization."""
from __future__ import annotations
import phonenumbers
from .chatdb import has_imessage_handle


def normalize_phone(raw: str, default_region: str = "IT") -> str | None:
    try:
        p = phonenumbers.parse(raw, default_region)
        if not phonenumbers.is_valid_number(p):
            return None
        return phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return None


def pick_imessage_handle(phones: list[str], emails: list[str],
                         db_path: str = "~/Library/Messages/chat.db",
                         default_region: str = "IT") -> tuple[str | None, str]:
    """Return (handle, type) where type in {'phone','email','none'}."""
    """Return (handle, type) where type in {'phone','email','none'}.
    Prefers a phone with confirmed iMessage history, then email, else None."""
    for raw in phones:
        e164 = normalize_phone(raw, default_region)
        if e164 and has_imessage_handle(e164, db_path):
            return e164, "phone"
    for em in emails:
        em_l = em.strip().lower()
        if em_l and has_imessage_handle(em_l, db_path):
            return em_l, "email"
    return None, "none"
