from app.merger.merge_engine import MergeEngine


def test_merge_union_and_resume_priority():
    csv_data = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "headline": "AI Intern",
    }

    resume_data = {
        "full_name": "John D.",
        "emails": ["JOHN@gmail.com"],
        "skills": ["python", "reactjs"],
        "headline": "Software Engineer Intern",
    }

    result = MergeEngine().merge(csv_data, resume_data)

    assert result["full_name"] == "John D."
    assert result["headline"] == "Software Engineer Intern"
    assert result["emails"] == ["john@gmail.com"]
    assert "python" in result["skills"]
    assert "react" in result["skills"]
    assert len(result["conflict_report"]) >= 1


def test_merge_tracks_conflicts():
    csv_data = {"full_name": "Alice Smith", "headline": "Data Analyst"}
    resume_data = {"full_name": "Alice A. Smith", "headline": "ML Engineer"}

    result = MergeEngine().merge(csv_data, resume_data)
    conflict_fields = {entry["field"] for entry in result["conflict_report"]}

    assert "full_name" in conflict_fields or "headline" in conflict_fields


def test_invalid_csv_phone_does_not_poison_valid_resume_phone():
    csv_data = {"phones": ["91xx87625h"]}
    resume_data = {"phones": ["9150281501"]}

    result = MergeEngine().merge(csv_data, resume_data)

    assert result["phones"] == ["+919150281501"]
    phone_conflicts = [
        entry for entry in result["conflict_report"] if entry["field"] == "phones"
    ]
    assert len(phone_conflicts) == 1
    assert phone_conflicts[0]["reason"] == "valid_value_priority"
    assert phone_conflicts[0]["selected"] == ["+919150281501"]
    invalid_values = [
        value
        for value in phone_conflicts[0]["values"]
        if value["status"] == "invalid"
    ]
    assert invalid_values
    assert invalid_values[0]["raw_value"] == "91xx87625h"


def test_invalid_phone_in_both_sources_yields_empty_phones():
    csv_data = {"phones": ["91xx87625h"]}
    resume_data = {"phones": ["abcdefghij"]}

    result = MergeEngine().merge(csv_data, resume_data)

    assert result["phones"] == []


def test_duplicate_phones_deduplicated():
    csv_data = {"phones": ["9150281501"]}
    resume_data = {"phones": ["+91 9150281501"]}

    result = MergeEngine().merge(csv_data, resume_data)

    assert result["phones"] == ["+919150281501"]
