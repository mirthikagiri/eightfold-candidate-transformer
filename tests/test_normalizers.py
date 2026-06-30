from app.normalizers.email import normalize_email, normalize_email_with_report
from app.normalizers.location import normalize_location
from app.normalizers.phone import (
    normalize_phone,
    normalize_phone_detailed,
    normalize_phone_with_report,
)
from app.normalizers.skills import normalize_skill


def test_email_normalization():
    assert normalize_email("  JOHN@GMAIL.COM  ") == "john@gmail.com"
    assert normalize_email(None) is None


def test_invalid_email_rejected():
    assert normalize_email("not-an-email") is None


def test_skill_alias_mapping():
    assert normalize_skill("reactjs") == "react"
    assert normalize_skill("node.js") == "nodejs"
    assert normalize_skill("express.js") == "express"
    assert normalize_skill("unknown-skill") == "unknown-skill"


def test_phone_normalization_indian():
    assert normalize_phone("9876543210") == "+919876543210"


def test_phone_formats_normalize_to_e164():
    assert normalize_phone("9150281501") == "+919150281501"
    assert normalize_phone("+91 9150281501") == "+919150281501"
    assert normalize_phone("+91-9150281501") == "+919150281501"
    assert normalize_phone("91 9150281501") == "+919150281501"
    assert normalize_phone("(91)9150281501") == "+919150281501"


def test_phone_invalid_number():
    assert normalize_phone("+91 9150XX9870") is None
    assert normalize_phone("91xx87625h") is None
    assert normalize_phone("abcdefghij") is None
    assert normalize_phone("123") is None


def test_phone_normalization_report_invalid():
    value, entry = normalize_phone_with_report(
        "91xx87625h",
        source="recruiter_csv",
    )

    assert value is None
    assert entry["status"] == "invalid"
    assert entry["reason"] == "invalid_phone_format"
    assert entry["normalized_value"] is None


def test_phone_normalization_report_valid():
    value, entry = normalize_phone_with_report(
        "9150281501",
        source="resume_pdf",
    )

    assert value == "+919150281501"
    assert entry["status"] == "valid"
    assert entry["normalized_value"] == "+919150281501"


def test_phone_detailed_status():
    value, status, reason = normalize_phone_detailed("123")
    assert value is None
    assert status == "invalid"
    assert reason == "phone_too_short"


def test_email_normalization_report():
    value, entry = normalize_email_with_report(
        "bad-email",
        source="recruiter_csv",
    )

    assert value is None
    assert entry["status"] == "invalid"
    assert entry["reason"] == "invalid_email_format"


def test_location_normalization():
    assert normalize_location("Chennai, India") == {
        "city": "Chennai",
        "country": "IN",
    }
