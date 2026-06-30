from app.projection.models import FieldRule, ProjectionPlan
from app.validation.validator import ProjectionValidator


def test_validator_required_field_error():
    plan = ProjectionPlan(
        fields=[FieldRule(path="candidate_name", required=True)],
    )
    result = ProjectionValidator().validate({"candidate_name": None}, plan)

    assert "candidate_name is required" in result["errors"]


def test_validator_missing_optional_warning():
    plan = ProjectionPlan(
        fields=[FieldRule(path="primary_phone", required=False)],
    )
    result = ProjectionValidator().validate({}, plan)

    assert "primary_phone is missing" in result["warnings"]
