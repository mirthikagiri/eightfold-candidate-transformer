import pytest

from app.projection.models import FieldRule, ProjectionPlan
from app.projection.projector import ProjectionEngine


def test_missing_null():
    projector = ProjectionEngine()
    plan = ProjectionPlan(
        fields=[FieldRule(path="phone")],
        on_missing="null",
    )

    output = projector.project({}, plan)
    assert output["phone"] is None


def test_missing_omit():
    projector = ProjectionEngine()
    plan = ProjectionPlan(
        fields=[FieldRule(path="phone")],
        on_missing="omit",
    )

    output = projector.project({}, plan)
    assert "phone" not in output


def test_missing_error():
    projector = ProjectionEngine()
    plan = ProjectionPlan(
        fields=[FieldRule(path="phone", required=True)],
        on_missing="error",
    )

    with pytest.raises(ValueError, match="Missing field"):
        projector.project({}, plan)
