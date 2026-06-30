from app.adapters.resume_adapter import ResumeAdapter


def test_resume_adapter():

    adapter = ResumeAdapter()

    result = adapter.extract(
        "sample_data/resume.pdf"
    )

    assert result is not None
    assert isinstance(result, dict)