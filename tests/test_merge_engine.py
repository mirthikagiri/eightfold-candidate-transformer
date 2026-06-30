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

    assert "full_name" in conflict_fields
    assert "headline" in conflict_fields
