from app.normalizers.email import normalize_email
from app.normalizers.location import normalize_location
from app.normalizers.phone import normalize_phone
from app.normalizers.skills import normalize_skill


def test_email_normalization():
    assert normalize_email("  JOHN@GMAIL.COM  ") == "john@gmail.com"
    assert normalize_email(None) is None


def test_skill_alias_mapping():
    assert normalize_skill("reactjs") == "react"
    assert normalize_skill("node.js") == "nodejs"
    assert normalize_skill("express.js") == "express"
    assert normalize_skill("unknown-skill") == "unknown-skill"


def test_phone_normalization_indian():
    assert normalize_phone("9876543210") == "+919876543210"


def test_phone_invalid_number():
    assert normalize_phone("+91 9150XX9870") is None


def test_location_normalization():
    assert normalize_location("Chennai, India") == {
        "city": "Chennai",
        "country": "IN",
    }
