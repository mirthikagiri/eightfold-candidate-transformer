from app.projection.models import FieldRule, ProjectionPlan
from app.validation.validator import ProjectionValidator


def test_validator_required_field_error():
    plan = ProjectionPlan(
        fields=[FieldRule(path="candidate_name", required=True)],
    )
    result = ProjectionValidator().validate(
        {"candidate_name": None},
        plan,
    )["validation"]

    assert result["passed"] is False
    assert result["errors"][0]["field"] == "candidate_name"
    assert result["errors"][0]["message"] == "candidate_name is required"


def test_validator_missing_optional_warning():
    plan = ProjectionPlan(
        fields=[FieldRule(path="primary_phone", required=False)],
    )
    result = ProjectionValidator().validate({}, plan)["validation"]

    assert result["passed"] is True
    assert result["warnings"][0]["message"] == "primary_phone is missing"
