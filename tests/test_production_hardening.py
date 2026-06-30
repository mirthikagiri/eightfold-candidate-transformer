import json
import tempfile
from pathlib import Path

import pytest

from app.merger.conflict_resolver import ConflictResolver
from app.merger.merge_engine import MergeEngine
from app.merger.provenance import ProvenanceTracker
from app.projection.compiler import ConfigCompiler
from app.projection.config_validator import ConfigValidationError, ConfigValidator
from app.projection.models import FieldRule, ProjectionPlan
from app.quality.report import QualityReport
from app.confidence.scorer import ConfidenceScorer
from app.validation.validator import ProjectionValidator


def test_invalid_phone_conflict_preserves_raw_value():
    csv_data = {"phones": ["91xx87625h"]}
    resume_data = {"phones": ["9150281501"]}

    result = MergeEngine().merge(csv_data, resume_data)
    conflict = next(
        entry for entry in result["conflict_report"] if entry["field"] == "phones"
    )

    csv_entry = next(
        value for value in conflict["values"] if value["source"] == "recruiter_csv"
    )
    resume_entry = next(
        value for value in conflict["values"] if value["source"] == "resume_pdf"
    )

    assert csv_entry["raw_value"] == "91xx87625h"
    assert csv_entry["normalized_value"] is None
    assert csv_entry["status"] == "invalid"
    assert resume_entry["raw_value"] == "9150281501"
    assert resume_entry["normalized_value"] == "+919150281501"
    assert resume_entry["status"] == "valid"
    assert conflict["reason"] == "valid_value_priority"


def test_invalid_email_conflict_preserves_raw_value():
    csv_data = {"emails": ["bad-email"]}
    resume_data = {"emails": ["john@gmail.com"]}

    result = MergeEngine().merge(csv_data, resume_data)

    assert result["emails"] == ["john@gmail.com"]
    conflict = next(
        entry for entry in result["conflict_report"] if entry["field"] == "emails"
    )
    invalid = next(
        value for value in conflict["values"] if value["status"] == "invalid"
    )
    assert invalid["raw_value"] == "bad-email"
    assert invalid["normalized_value"] is None


def test_conflict_resolver_collection_includes_invalid_candidates():
    resolver = ConflictResolver()
    decision = resolver.resolve_collection(
        field="phones",
        csv_items=[
            {
                "source": "recruiter_csv",
                "value": None,
                "raw_value": "91xx87625h",
                "status": "invalid",
            }
        ],
        resume_items=[
            {
                "source": "resume_pdf",
                "value": "+919150281501",
                "raw_value": "9150281501",
                "status": "valid",
            }
        ],
    )

    assert len(decision["conflict"]["values"]) == 2
    assert decision["conflict"]["values"][0]["raw_value"] == "91xx87625h"


def test_identity_mismatch_warning():
    plan = ProjectionPlan(fields=[], identity_warning_threshold=0.50)
    report = ProjectionValidator().validate(
        {},
        plan,
        identity={"identity_score": 0.12, "match_keys": []},
    )["validation"]

    identity_warnings = [
        warning for warning in report["warnings"] if warning["field"] == "_identity"
    ]
    assert len(identity_warnings) == 1
    assert "0.12" in identity_warnings[0]["message"]
    assert report["passed"] is True


def test_identity_match_no_warning():
    plan = ProjectionPlan(fields=[], identity_warning_threshold=0.50)
    report = ProjectionValidator().validate(
        {},
        plan,
        identity={"identity_score": 0.95, "match_keys": ["email"]},
    )["validation"]

    assert not any(w["field"] == "_identity" for w in report["warnings"])


def test_config_validator_missing_fields_key():
    result = ConfigValidator().validate({})
    assert result["valid"] is False
    assert "Config missing required key: fields" in result["errors"]


def test_config_validator_invalid_on_missing():
    result = ConfigValidator().validate({"fields": [{"path": "name"}], "on_missing": "skip"})
    assert any("Invalid on_missing" in error for error in result["errors"])


def test_config_validator_invalid_field_path():
    result = ConfigValidator().validate({"fields": [{"required": True}]})
    assert any("missing required property: path" in error for error in result["errors"])


def test_config_compiler_raises_structured_error_for_invalid_config():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as handle:
        json.dump({"on_missing": "invalid"}, handle)
        path = handle.name

    with pytest.raises(ConfigValidationError) as exc:
        ConfigCompiler().compile(path)

    assert any("fields" in error for error in exc.value.errors)
    Path(path).unlink(missing_ok=True)


def test_item_level_phone_provenance():
    csv_data = {"phones": ["91xx87625h"]}
    resume_data = {"phones": ["9150281501"]}
    canonical = MergeEngine().merge(csv_data, resume_data)

    provenance = ProvenanceTracker().build(csv_data, resume_data, canonical)

    assert provenance["phones"]["sources"]
    assert provenance["phones"]["items"] == [
        {"value": "+919150281501", "source": "resume_pdf"}
    ]


def test_item_level_email_provenance():
    csv_data = {"emails": ["john@gmail.com"]}
    resume_data = {"emails": ["john@gmail.com"]}
    canonical = MergeEngine().merge(csv_data, resume_data)

    provenance = ProvenanceTracker().build(csv_data, resume_data, canonical)

    assert provenance["emails"]["items"][0]["value"] == "john@gmail.com"
    assert set(provenance["emails"]["items"][0]["sources"]) == {
        "recruiter_csv",
        "resume_pdf",
    }


def test_item_level_skill_provenance():
    csv_data = {"skills": ["python"]}
    resume_data = {"skills": ["reactjs"]}
    canonical = MergeEngine().merge(csv_data, resume_data)

    provenance = ProvenanceTracker().build(csv_data, resume_data, canonical)

    items = {item["value"]: item for item in provenance["skills"]["items"]}
    assert items["python"]["source"] == "recruiter_csv"
    assert items["react"]["source"] == "resume_pdf"


def test_trust_score_matches_overall_confidence_logic():
    canonical = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "phones": ["+919876543210"],
        "skills": ["python"],
        "provenance": {
            "full_name": {"sources": ["resume_pdf", "recruiter_csv"]},
            "emails": {"sources": ["resume_pdf", "recruiter_csv"]},
            "phones": {"sources": ["resume_pdf"]},
            "skills": {"sources": ["resume_pdf"]},
        },
        "conflict_report": [],
    }
    csv_data = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "phones": ["9876543210"],
        "skills": ["python"],
    }
    resume_data = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "phones": ["+919876543210"],
        "skills": ["python"],
    }

    scores, overall = ConfidenceScorer().score_profile(
        canonical,
        csv_data,
        resume_data,
    )
    canonical["overall_confidence"] = overall
    report = QualityReport().generate(canonical, scores)

    assert report["trust_score"] == round(overall * 100)
    assert report["overall_confidence"] == overall


def test_duplicate_phones_merge_and_provenance():
    csv_data = {"phones": ["9150281501"]}
    resume_data = {"phones": ["+91 9150281501"]}
    canonical = MergeEngine().merge(csv_data, resume_data)

    assert canonical["phones"] == ["+919150281501"]
    provenance = ProvenanceTracker().build(csv_data, resume_data, canonical)
    assert len(provenance["phones"]["items"]) == 1


def test_duplicate_emails_merge_and_provenance():
    csv_data = {"emails": ["John@Gmail.com"]}
    resume_data = {"emails": ["john@gmail.com"]}
    canonical = MergeEngine().merge(csv_data, resume_data)

    assert canonical["emails"] == ["john@gmail.com"]
    provenance = ProvenanceTracker().build(csv_data, resume_data, canonical)
    assert provenance["emails"]["items"][0]["sources"] == [
        "recruiter_csv",
        "resume_pdf",
    ]


def test_pipeline_config_error_does_not_crash():
    from app.services.pipeline import CandidatePipeline

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as handle:
        json.dump({"on_missing": "bad"}, handle)
        path = handle.name

    result = CandidatePipeline().run(
        csv_path="sample_data/recruiter.csv",
        resume_path="sample_data/resume.pdf",
        config_path=path,
    )
    Path(path).unlink(missing_ok=True)

    assert result["config_errors"]
    assert result["canonical"] is None
    assert result["validation"]["passed"] is False


def test_projection_includes_validation_when_enabled():
    from app.projection.projector import ProjectionEngine

    plan = ProjectionPlan(
        fields=[FieldRule(path="candidate_name", from_field="full_name")],
        include_validation=False,
    )
    canonical = {"full_name": "Jane Doe"}
    projection = ProjectionEngine().project(canonical, plan)
    assert "_validation" not in projection.output
