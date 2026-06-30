def normalize_email(email: str | None) -> str | None:
    """
    Normalize email addresses.

    Example:
    JOHN@GMAIL.COM
    ->
    john@gmail.com
    """

    if not email:
        return None

    return email.strip().lower()