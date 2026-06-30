from app.quality.report import QualityReport


def test_quality_report_scores():
    canonical = {
        "candidate_id": "cand_123",
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "phones": [],
        "skills": ["python"],
        "conflict_report": [{"field": "headline"}],
        "source_count": 2,
    }
    confidence = {"full_name": 0.95, "emails": 0.95, "skills": 0.90}

    report = QualityReport().generate(canonical, confidence)

    assert report["source_count"] == 2
    assert report["conflicts_detected"] == 1
    assert report["quality_score"] > 0
    assert "phones" in report["missing_fields"]
