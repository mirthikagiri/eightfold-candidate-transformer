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
        conflict_fields=set(),
        uncertain_fields=set(),
        invalid_fields=set(),
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
        conflict_fields={"headline"},
        uncertain_fields=set(),
        invalid_fields=set(),
    )

    assert score == 0.80


def test_confidence_validation_bonus_for_phones():
    canonical = {
        "phones": ["+919150281501"],
        "provenance": {
            "phones": {
                "sources": ["resume_pdf"],
            }
        },
        "conflict_report": [],
    }

    score = ConfidenceScorer().score_field(
        "phones",
        canonical,
        {},
        {"phones": ["+919150281501"]},
        conflict_fields=set(),
        uncertain_fields=set(),
        invalid_fields=set(),
    )

    assert score == 0.95


def test_confidence_invalid_source_penalty():
    canonical = {
        "phones": ["+919150281501"],
        "provenance": {
            "phones": {
                "sources": ["resume_pdf", "recruiter_csv"],
            }
        },
        "conflict_report": [],
    }

    score = ConfidenceScorer().score_field(
        "phones",
        canonical,
        {"phones": ["91xx87625h"]},
        {"phones": ["+919150281501"]},
        conflict_fields=set(),
        uncertain_fields={"phones"},
        invalid_fields={"phones"},
    )

    assert score == 0.85


def test_confidence_missing_critical_field():
    scorer = ConfidenceScorer()
    canonical = {
        "full_name": None,
        "emails": ["john@gmail.com"],
        "phones": ["+919150281501"],
        "provenance": {
            "emails": {"sources": ["resume_pdf"]},
            "phones": {"sources": ["resume_pdf"]},
        },
        "conflict_report": [],
    }

    scores, overall = scorer.score_profile(
        canonical,
        {"emails": ["john@gmail.com"], "phones": ["+919150281501"]},
        {},
    )

    assert scores["full_name"] == 0.0
    assert overall > 0.65
