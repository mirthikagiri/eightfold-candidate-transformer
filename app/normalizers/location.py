import re
from typing import Any, Dict, Optional

COUNTRY_ALIASES = {
    "india": "IN",
    "in": "IN",
    "usa": "US",
    "us": "US",
    "united states": "US",
    "uk": "GB",
    "united kingdom": "GB",
}


def normalize_location(value: Any) -> Optional[Dict[str, Optional[str]]]:
    """
    Normalize location strings like "Chennai, India" into structured form.

    Returns:
        {"city": "Chennai", "country": "IN"} or None
    """
    if not value:
        return None

    if isinstance(value, dict):
        city = value.get("city")
        country = value.get("country")
        if not city and not country:
            return None
        normalized_country = _normalize_country(country) if country else None
        return {
            "city": city.strip() if isinstance(city, str) else city,
            "country": normalized_country,
        }

    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    parts = [part.strip() for part in text.split(",") if part.strip()]
    if not parts:
        return None

    if len(parts) == 1:
        return {"city": parts[0], "country": None}

    city = parts[0]
    country = _normalize_country(parts[-1])
    return {"city": city, "country": country}


def _normalize_country(country: Optional[str]) -> Optional[str]:
    if not country:
        return None

    text = country.strip()
    if not text:
        return None

    if len(text) == 2 and text.isalpha():
        return text.upper()

    alias = COUNTRY_ALIASES.get(text.lower())
    if alias:
        return alias

    return text.upper() if len(text) == 2 else text


def location_to_string(location: Optional[Dict[str, Any]]) -> Optional[str]:
    if not location:
        return None

    city = location.get("city")
    country = location.get("country")
    if city and country:
        return f"{city}, {country}"
    return city or country
