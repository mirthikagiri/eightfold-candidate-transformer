from app.projection.projector import (
    ProjectionEngine
)

from app.projection.models import (
    ProjectionPlan,
    FieldRule
)


def test_missing_null():

    projector = ProjectionEngine()

    plan = ProjectionPlan(
        fields=[
            FieldRule(
                path="phone"
            )
        ],
        on_missing="null"
    )

    output = projector.project(
        {},
        plan
    )

    assert output["phone"] is None