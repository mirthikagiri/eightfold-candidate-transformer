from app.normalizers.email import normalize_email
from app.normalizers.phone import normalize_phone
from app.normalizers.skills import normalize_skill


def test_email_normalization():
    assert normalize_email(
        "JOHN@GMAIL.COM"
    ) == "john@gmail.com"


def test_skill_normalization():
    assert normalize_skill(
        "reactjs"
    ) == "react"


def test_phone_normalization():
    assert normalize_phone(
        "9876543210"
    ) == "+919876543210"