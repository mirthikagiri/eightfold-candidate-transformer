from app.merger.audit import AuditTrail
from app.merger.merge_engine import MergeEngine
from app.quality.report import QualityReport


def test_audit_trail_includes_resolution_details():
    csv_data = {"phones": ["91xx87625h"]}
    resume_data = {"phones": ["9150281501"]}
    canonical = MergeEngine().merge(csv_data, resume_data)
    canonical["provenance"] = {
        "phones": {
            "sources": ["recruiter_csv", "resume_pdf"],
            "method": "merge",
            "resolution_policy": "valid_value_priority",
        }
    }
    confidence = {"phones": 0.95}

    audit = AuditTrail().generate(canonical, confidence)

    assert audit["phones"]["selected_value"] == ["+919150281501"]
    assert audit["phones"]["resolution_policy"] == "valid_value_priority"
    assert audit["phones"]["normalizations"] == ["E164"]
    assert len(audit["phones"]["candidate_values"]) >= 1


def test_quality_report_includes_normalization_failures():
    canonical = {
        "candidate_id": "cand_123",
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "phones": ["+919150281501"],
        "skills": ["python"],
        "conflict_report": [{"field": "phones", "reason": "valid_value_priority"}],
        "normalization_report": [
            {
                "field": "phone",
                "status": "invalid",
                "reason": "invalid_phone_format",
            }
        ],
        "source_count": 2,
    }
    confidence = {
        "full_name": 0.95,
        "emails": 0.95,
        "phones": 0.85,
        "skills": 0.90,
    }

    report = QualityReport().generate(canonical, confidence)

    assert report["normalization_failures"] == 1
    assert report["conflicts_detected"] == 1
    assert report["quality_score"] > 0
