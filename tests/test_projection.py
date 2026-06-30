from app.projection.projector import ProjectionEngine
from app.projection.compiler import ConfigCompiler


def test_projection_with_nested_path():
    canonical = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "phones": ["+919876543210"],
        "location": {"city": "Chennai", "country": "IN"},
        "skills": ["python"],
        "confidence": {"full_name": 0.95},
        "provenance": {"full_name": {"sources": ["resume_pdf"]}},
        "quality_report": {"quality_score": 90},
        "_audit": {"full_name": {"confidence": 0.95}},
        "conflict_report": [],
        "normalization_report": [],
    }

    plan = ConfigCompiler().compile("configs/default.json")
    projection = ProjectionEngine().project(canonical, plan)
    output = projection.output

    assert output["candidate_name"] == "John Doe"
    assert output["primary_email"] == "john@gmail.com"
    assert output["location_city"] == "Chennai"
    assert "_quality" in output
    assert "_audit" in output
    assert "_conflicts" in output
    assert "_normalization_report" in output


def test_pipeline_attaches_validation_when_configured():
    from app.services.pipeline import CandidatePipeline

    result = CandidatePipeline().run(
        csv_path="sample_data/recruiter.csv",
        resume_path="sample_data/resume.pdf",
        config_path="configs/default.json",
    )

    assert "_validation" in result["projected"]
    assert "passed" in result["projected"]["_validation"]
