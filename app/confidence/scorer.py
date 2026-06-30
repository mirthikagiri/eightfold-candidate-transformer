from typing import Any, Dict, List, Tuple


class ConfidenceScorer:
    SOURCE_WEIGHTS = {
        "resume_pdf": 0.90,
        "recruiter_csv": 0.80,
    }

    AGREEMENT_BONUS = 0.05
    CONFLICT_PENALTY = 0.10
    UNCERTAINTY_PENALTY = 0.15

    METADATA_FIELDS = {
        "source_count",
        "conflict_report",
        "_merge_decisions",
        "provenance",
        "confidence",
        "overall_confidence",
        "quality_report",
        "_audit",
        "candidate_id",
        "identity",
    }

    def score_field(
        self,
        field_name: str,
        canonical: Dict[str, Any],
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        conflict_fields: List[str],
        uncertain_fields: List[str],
    ) -> float:
        provenance = canonical.get("provenance", {}).get(field_name, {})
        sources = provenance.get("sources", [])

        if not sources:
            return 0.0

        if len(sources) == 2:
            base = max(self.SOURCE_WEIGHTS.values())
        elif sources[0] == "resume_pdf":
            base = self.SOURCE_WEIGHTS["resume_pdf"]
        else:
            base = self.SOURCE_WEIGHTS["recruiter_csv"]

        score = base

        if len(sources) == 2 and field_name not in conflict_fields:
            score += self.AGREEMENT_BONUS

        if field_name in conflict_fields:
            score -= self.CONFLICT_PENALTY

        if field_name in uncertain_fields:
            score -= self.UNCERTAINTY_PENALTY

        return round(max(0.0, min(1.0, score)), 2)

    def score_profile(
        self,
        canonical: Dict[str, Any],
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> Tuple[Dict[str, float], float]:
        conflict_fields = [
            entry["field"] for entry in canonical.get("conflict_report", [])
        ]
        uncertain_fields = list(
            set(
                (csv_data.get("_uncertain_fields") or [])
                + (resume_data.get("_uncertain_fields") or [])
            )
        )

        scores: Dict[str, float] = {}

        for field in canonical:
            if field in self.METADATA_FIELDS:
                continue

            scores[field] = self.score_field(
                field,
                canonical,
                csv_data,
                resume_data,
                conflict_fields,
                uncertain_fields,
            )

        if scores:
            overall = round(sum(scores.values()) / len(scores), 2)
        else:
            overall = 0.0

        return scores, overall
