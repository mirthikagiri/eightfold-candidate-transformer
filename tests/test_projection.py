from app.projection.projector import ProjectionEngine
from app.projection.compiler import ConfigCompiler


def test_projection():

    canonical = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "skills": ["python"]
    }

    compiler = ConfigCompiler()

    plan = compiler.compile(
        "configs/default.json"
    )

    projector = ProjectionEngine()

    output = projector.project(
        canonical,
        plan
    )

    assert output["candidate_name"] == "John Doe"
    assert output["primary_email"] == ["john@gmail.com"] or output["primary_email"] == "john@gmail.com"