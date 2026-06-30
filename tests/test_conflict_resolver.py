from app.merger.conflict_resolver import ConflictResolver


def test_valid_value_priority_over_source():
    resolver = ConflictResolver()

    decision = resolver.resolve_scalar(
        field="phones",
        csv_value="91xx87625h",
        resume_value="+919150281501",
        csv_source="recruiter_csv",
        resume_source="resume_pdf",
        prefer="recruiter_csv",
        policy="resume_priority",
        csv_status="invalid",
        resume_status="valid",
    )

    assert decision["selected"] == "+919150281501"
    assert decision["resolution_policy"] == "valid_value_priority"
    assert decision["conflict"]["reason"] == "valid_value_priority"


def test_collection_valid_value_priority():
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

    assert decision["selected"] == ["+919150281501"]
    assert decision["resolution_policy"] == "valid_value_priority"
