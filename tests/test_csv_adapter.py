from app.adapters.csv_adapter import CSVAdapter


def test_csv_adapter():
    adapter = CSVAdapter()

    result = adapter.extract(
        "sample_data/recruiter.csv"
    )

    assert result is not None
    assert "full_name" in result