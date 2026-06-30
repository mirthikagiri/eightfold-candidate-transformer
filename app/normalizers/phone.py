import re
from typing import Any, Dict, Optional, Tuple

import phonenumbers

from app.normalizers.result import make_normalization_entry


def _contains_invalid_letters(phone: str) -> bool:
    """Reject phones containing alphabetic characters (e.g. 91xx87625h)."""
    return bool(re.search(r"[a-zA-Z]", phone))


def _preprocess_phone(phone: str) -> str:
    """Normalize common Indian phone formatting before parsing."""
    cleaned = phone.strip()
    cleaned = re.sub(r"^\((\d{1,3})\)", r"+\1", cleaned)
    cleaned = cleaned.replace("-", " ").replace("(", "").replace(")", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _phone_failure_reason(phone: str, region: str) -> str:
    if not re.search(r"\d", phone):
        return "invalid_phone_format"
    if _contains_invalid_letters(phone):
        return "invalid_phone_format"
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10:
        return "phone_too_short"
    try:
        parsed = phonenumbers.parse(_preprocess_phone(phone), region)
        if not phonenumbers.is_valid_number(parsed):
            return "invalid_phone_number"
    except Exception:
        return "invalid_phone_format"
    return "invalid_phone_format"


def normalize_phone(phone: str | None, region: str = "IN") -> str | None:
    """
    Convert phone number to E.164 format.

    Example:
    9876543210 -> +919876543210
    """
    value, _status, _reason = _normalize_phone_internal(phone, region)
    return value


def normalize_phone_detailed(
    phone: str | None,
    region: str = "IN",
) -> Tuple[Optional[str], str, Optional[str]]:
    """Return normalized value, status, and optional failure reason."""
    return _normalize_phone_internal(phone, region)


def normalize_phone_with_report(
    phone: str | None,
    source: str,
    field: str = "phone",
    region: str = "IN",
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Normalize a phone and produce a normalization report entry."""
    normalized, status, reason = _normalize_phone_internal(phone, region)
    entry = make_normalization_entry(
        field=field,
        source=source,
        raw_value=phone,
        normalized_value=normalized,
        status=status,
        reason=reason if status == "invalid" else None,
    )
    return normalized, entry


def _normalize_phone_internal(
    phone: str | None,
    region: str = "IN",
) -> Tuple[Optional[str], str, Optional[str]]:
    if not phone:
        return None, "invalid", "empty_value"

    raw = str(phone).strip()
    if not raw:
        return None, "invalid", "empty_value"

    if _contains_invalid_letters(raw):
        return None, "invalid", "invalid_phone_format"

    try:
        parsed = phonenumbers.parse(_preprocess_phone(raw), region)
        if phonenumbers.is_valid_number(parsed):
            formatted = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164,
            )
            return formatted, "valid", None
    except Exception:
        pass

    return None, "invalid", _phone_failure_reason(raw, region)
