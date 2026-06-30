from app.confidence.scorer import ConfidenceScorer


def test_confidence_agreement_bonus():
    canonical = {
        "full_name": "John Doe",
        "provenance": {
            "full_name": {
                "sources": ["resume_pdf", "recruiter_csv"],
            }
        },
        "conflict_report": [],
    }

    score = ConfidenceScorer().score_field(
        "full_name",
        canonical,
        {"full_name": "John Doe"},
        {"full_name": "John Doe"},
        conflict_fields=[],
        uncertain_fields=[],
    )

    assert score == 0.95


def test_confidence_conflict_penalty():
    canonical = {
        "headline": "Engineer",
        "provenance": {
            "headline": {
                "sources": ["resume_pdf", "recruiter_csv"],
            }
        },
        "conflict_report": [{"field": "headline"}],
    }

    score = ConfidenceScorer().score_field(
        "headline",
        canonical,
        {"headline": "AI Intern"},
        {"headline": "Software Engineer"},
        conflict_fields=["headline"],
        uncertain_fields=[],
    )

    assert score == 0.80
