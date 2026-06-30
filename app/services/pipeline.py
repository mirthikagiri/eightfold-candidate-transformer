from typing import Any, Dict

from app.adapters.csv_adapter import CSVAdapter
from app.adapters.resume_adapter import ResumeAdapter
from app.canonical.schema import validate_canonical
from app.confidence.scorer import ConfidenceScorer
from app.merger.audit import AuditTrail
from app.merger.identity_resolver import IdentityResolver
from app.merger.merge_engine import MergeEngine
from app.merger.provenance import ProvenanceTracker
from app.normalizers.result import NormalizationReport
from app.projection.compiler import ConfigCompiler
from app.projection.projector import ProjectionEngine
from app.quality.report import QualityReport
from app.validation.validator import ProjectionValidator


class CandidatePipeline:

    def run(
        self,
        csv_path: str,
        resume_path: str,
        config_path: str,
    ) -> Dict[str, Any]:
        csv_data = CSVAdapter().extract(csv_path)
        resume_data = ResumeAdapter().extract(resume_path)

        identity = IdentityResolver().resolve(csv_data, resume_data)
        candidate_id = IdentityResolver().generate_candidate_id(
            csv_data,
            resume_data,
        )

        canonical = MergeEngine().merge(csv_data, resume_data)
        canonical["candidate_id"] = candidate_id
        canonical["identity"] = identity

        csv_report = NormalizationReport()
        csv_report.extend(csv_data.get("_normalization_report", []))
        resume_report = NormalizationReport()
        resume_report.extend(resume_data.get("_normalization_report", []))
        normalization_report = NormalizationReport.merge(csv_report, resume_report)
        canonical["normalization_report"] = normalization_report.to_list()

        provenance = ProvenanceTracker().build(
            csv_data,
            resume_data,
            canonical,
        )
        canonical["provenance"] = provenance

        confidence_scores, overall_confidence = ConfidenceScorer().score_profile(
            canonical,
            csv_data,
            resume_data,
        )
        canonical["confidence"] = confidence_scores
        canonical["overall_confidence"] = overall_confidence

        audit = AuditTrail().generate(canonical, confidence_scores)
        canonical["_audit"] = audit

        quality_report = QualityReport().generate(
            canonical,
            confidence_scores,
        )
        canonical["quality_report"] = quality_report

        validate_canonical(canonical)

        plan = ConfigCompiler().compile(config_path)
        projection = ProjectionEngine().project(canonical, plan)
        validation_report = ProjectionValidator().validate(
            projection.output,
            plan,
            projection.missing_events,
        )
        validation = validation_report["validation"]

        return {
            "canonical": canonical,
            "projected": projection.output,
            "validation": validation,
            "missing_events": projection.missing_events,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
        }
