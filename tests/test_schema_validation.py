from unittest.mock import patch

from pydantic import BaseModel, ValidationError

from app.services.pipeline import CandidatePipeline


def _sample_validation_error() -> ValidationError:
    class _Strict(BaseModel):
        full_name: str

    try:
        _Strict.model_validate({"full_name": 123})
    except ValidationError as exc:
        return exc
    raise AssertionError("expected ValidationError")


def test_pipeline_returns_schema_errors_on_validation_failure():
    with patch(
        "app.services.pipeline.validate_canonical",
        side_effect=_sample_validation_error(),
    ):
        result = CandidatePipeline().run(
            csv_path="sample_data/recruiter.csv",
            resume_path="sample_data/resume.pdf",
            config_path="configs/default.json",
        )

    assert result["canonical"] is None
    assert result["schema_errors"]
    assert result["validation"]["passed"] is False
