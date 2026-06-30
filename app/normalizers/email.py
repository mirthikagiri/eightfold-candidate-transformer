import re
from typing import Any, Dict, Optional, Tuple

from app.normalizers.result import make_normalization_entry

_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def normalize_email(email: str | None) -> str | None:
    """
    Normalize and validate email addresses.

    Example:
    JOHN@GMAIL.COM -> john@gmail.com
    """
    value, _status, _reason = _normalize_email_internal(email)
    return value


def normalize_email_detailed(
    email: str | None,
) -> Tuple[Optional[str], str, Optional[str]]:
    """Return normalized value, status, and optional failure reason."""
    return _normalize_email_internal(email)


def normalize_email_with_report(
    email: str | None,
    source: str,
    field: str = "email",
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Normalize an email and produce a normalization report entry."""
    normalized, status, reason = _normalize_email_internal(email)
    entry = make_normalization_entry(
        field=field,
        source=source,
        raw_value=email,
        normalized_value=normalized,
        status=status,
        reason=reason if status == "invalid" else None,
    )
    return normalized, entry


def _normalize_email_internal(
    email: str | None,
) -> Tuple[Optional[str], str, Optional[str]]:
    if not email:
        return None, "invalid", "empty_value"

    cleaned = str(email).strip().lower()
    if not cleaned:
        return None, "invalid", "empty_value"

    if not _EMAIL_PATTERN.match(cleaned):
        return None, "invalid", "invalid_email_format"

    return cleaned, "valid", None
