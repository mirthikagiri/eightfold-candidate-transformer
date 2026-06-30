import phonenumbers


def normalize_phone(phone: str | None, region: str = "IN") -> str | None:
    """
    Convert phone number to E.164 format.

    Example:
    9876543210
    ->
    +919876543210
    """

    if not phone:
        return None

    try:
        parsed = phonenumbers.parse(phone, region)

        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )

        return None

    except Exception:
        return None