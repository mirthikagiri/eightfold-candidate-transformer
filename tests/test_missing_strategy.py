from app.projection.models import FieldRule, ProjectionPlan
from app.projection.projector import ProjectionEngine
from app.validation.validator import ProjectionValidator


def test_missing_null():
    projector = ProjectionEngine()
    plan = ProjectionPlan(
        fields=[FieldRule(path="phone")],
        on_missing="null",
    )

    result = projector.project({}, plan)

    assert result.output["phone"] is None
    assert len(result.missing_events) == 1
    assert result.missing_events[0] == {
        "field": "phone",
        "source_field": "phone",
        "strategy": "null",
        "action": "set_null",
        "reason": "missing",
    }


def test_missing_omit():
    projector = ProjectionEngine()
    plan = ProjectionPlan(
        fields=[FieldRule(path="phone")],
        on_missing="omit",
    )

    result = projector.project({}, plan)

    assert "phone" not in result.output
    assert result.missing_events[0]["action"] == "omitted"
    assert result.missing_events[0]["strategy"] == "omit"


def test_missing_error_does_not_raise():
    projector = ProjectionEngine()
    plan = ProjectionPlan(
        fields=[FieldRule(path="phone", required=True)],
        on_missing="error",
    )

    result = projector.project({}, plan)

    assert "phone" not in result.output
    assert result.missing_events[0]["action"] == "validation_error"
    assert result.missing_events[0]["strategy"] == "error"


def test_missing_null_validation_report():
    plan = ProjectionPlan(
        fields=[FieldRule(path="phone")],
        on_missing="null",
    )
    projection = ProjectionEngine().project({}, plan)
    report = ProjectionValidator().validate(
        projection.output,
        plan,
        projection.missing_events,
    )["validation"]

    assert report["passed"] is True
    assert report["missing_decisions"] == [
        {"field": "phone", "strategy": "null", "action": "set_null"}
    ]


def test_missing_omit_validation_warning():
    plan = ProjectionPlan(
        fields=[FieldRule(path="phone")],
        on_missing="omit",
    )
    projection = ProjectionEngine().project({}, plan)
    report = ProjectionValidator().validate(
        projection.output,
        plan,
        projection.missing_events,
    )["validation"]

    assert report["passed"] is True
    assert report["warnings"][0]["field"] == "phone"
    assert report["warnings"][0]["action"] == "omitted"
    assert report["warnings"][0]["message"] == "phone missing"


def test_missing_error_validation_report():
    plan = ProjectionPlan(
        fields=[FieldRule(path="phone"), FieldRule(path="primary_email")],
        on_missing="error",
    )
    projection = ProjectionEngine().project({}, plan)
    report = ProjectionValidator().validate(
        projection.output,
        plan,
        projection.missing_events,
    )["validation"]

    assert report["passed"] is False
    assert len(report["errors"]) == 2
    assert report["errors"][0]["severity"] == "error"
    assert report["errors"][0]["message"] == "Required field missing"
    assert {entry["field"] for entry in report["errors"]} == {
        "phone",
        "primary_email",
    }
