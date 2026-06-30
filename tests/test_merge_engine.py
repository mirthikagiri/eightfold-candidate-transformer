from app.merger.merge_engine import MergeEngine


def test_merge():

    csv_data = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"]
    }

    resume_data = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "skills": ["python"]
    }

    merger = MergeEngine()

    result = merger.merge(
        csv_data,
        resume_data
    )

    assert result["full_name"] == "John Doe"
    assert "python" in result["skills"]s