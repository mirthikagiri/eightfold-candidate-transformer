from app.merger.provenance import ProvenanceTracker


def test_provenance_merged_sources():
    csv_data = {"emails": ["john@gmail.com"]}
    resume_data = {"emails": ["john@gmail.com"]}
    canonical = {
        "emails": ["john@gmail.com"],
        "_merge_decisions": {
            "emails": {
                "sources": ["recruiter_csv", "resume_pdf"],
                "policy": "union_dedupe",
            }
        },
    }

    provenance = ProvenanceTracker().build(csv_data, resume_data, canonical)

    assert provenance["emails"]["method"] == "merged"
    assert set(provenance["emails"]["sources"]) == {
        "recruiter_csv",
        "resume_pdf",
    }
