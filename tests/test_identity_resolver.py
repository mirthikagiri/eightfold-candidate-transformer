from app.merger.identity_resolver import IdentityResolver


def test_identity_email_and_name_match():
    csv_data = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "phones": ["9876543210"],
    }
    resume_data = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "phones": ["+919876543210"],
    }

    result = IdentityResolver().resolve(csv_data, resume_data)

    assert result["identity_score"] >= 0.90
    assert "email" in result["match_keys"]
    assert "phone" in result["match_keys"]


def test_candidate_id_is_deterministic_from_email():
    csv_data = {"emails": ["john@gmail.com"]}
    resume_data = {}

    first = IdentityResolver().generate_candidate_id(csv_data, resume_data)
    second = IdentityResolver().generate_candidate_id(csv_data, resume_data)

    assert first == second
    assert first.startswith("cand_")
