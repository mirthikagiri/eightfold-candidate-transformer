from datetime import datetime


SUPPORTED_FORMATS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%b %Y",
    "%B %Y"
]


def normalize_date(date_str: str | None):

    if not date_str:
        return None

    for fmt in SUPPORTED_FORMATS:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)

            return parsed.strftime("%Y-%m-%d")

        except Exception:
            continue

    return None