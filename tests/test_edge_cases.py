from app.adapters.csv_adapter import CSVAdapter
from app.adapters.resume_adapter import ResumeAdapter
from app.merger.merge_engine import MergeEngine


def test_empty_csv_graceful():
    import pandas as pd
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        f.write("name,email,phone,current_company,title\n")
        path = f.name

    result = CSVAdapter().extract(path)
    merged = MergeEngine().merge(result, {"full_name": "Fallback"})

    assert merged["full_name"] == "Fallback"
    Path(path).unlink(missing_ok=True)


def test_empty_resume_graceful():
    result = ResumeAdapter().extract("sample_data/missing.pdf")
    assert result.get("source") == "resume_pdf"


def test_duplicate_emails_deduplicated():
    csv_data = {"emails": ["John@Gmail.com"]}
    resume_data = {"emails": ["john@gmail.com"]}

    merged = MergeEngine().merge(csv_data, resume_data)
    assert merged["emails"] == ["john@gmail.com"]


def test_invalid_email_not_included():
    csv_data = {"emails": ["bad-email"]}
    resume_data = {"emails": ["john@gmail.com"]}

    merged = MergeEngine().merge(csv_data, resume_data)
    assert merged["emails"] == ["john@gmail.com"]


def test_csv_invalid_phone_records_normalization_failure():
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        f.write("name,email,phone,current_company,title\n")
        f.write("Jane Doe,jane@gmail.com,91xx87625h,Acme,Engineer\n")
        path = f.name

    result = CSVAdapter().extract(path)
    invalid_entries = [
        entry
        for entry in result["_normalization_report"]
        if entry.get("status") == "invalid"
    ]

    assert result["phones"] == []
    assert len(invalid_entries) == 1
    assert invalid_entries[0]["reason"] == "invalid_phone_format"
    Path(path).unlink(missing_ok=True)
