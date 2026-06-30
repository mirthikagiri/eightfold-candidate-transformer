import json

from app.adapters.csv_adapter import CSVAdapter
from app.adapters.resume_adapter import ResumeAdapter

from app.merger.merge_engine import MergeEngine
from app.merger.provenance import ProvenanceTracker

from app.confidence.scorer import ConfidenceScorer

from app.quality.report import QualityReport

from app.projection.compiler import ConfigCompiler
from app.projection.projector import ProjectionEngine

from app.validation.validator import ProjectionValidator


class CandidatePipeline:

    def run(
        self,
        csv_path,
        resume_path,
        config_path
    ):

        csv_data = (
            CSVAdapter()
            .extract(csv_path)
        )

        resume_data = (
            ResumeAdapter()
            .extract(resume_path)
        )
        print(csv_data)
        print(resume_data)

        canonical = (
            MergeEngine()
            .merge(
                csv_data,
                resume_data
            )
        )
        print(canonical)

        provenance = (
            ProvenanceTracker()
            .build(
                csv_data,
                resume_data,
                canonical
            )
        )

        canonical["provenance"] = provenance

        confidence_scores, overall_confidence = (
            ConfidenceScorer()
            .score_profile(
                canonical,
                csv_data,
                resume_data
            )
        )

        canonical["confidence"] = (
            confidence_scores
        )

        canonical["overall_confidence"] = (
            overall_confidence
        )

        quality_report = (
            QualityReport()
            .generate(
                canonical,
                confidence_scores
            )
        )

        canonical["quality_report"] = (
            quality_report
        )

        plan = (
            ConfigCompiler()
            .compile(config_path)
        )

        output = (
            ProjectionEngine()
            .project(
                canonical,
                plan
            )
        )

        errors = (
            ProjectionValidator()
            .validate(
                output,
                plan
            )
        )

        return {
            "canonical": canonical,
            "projected": output,
            "errors": errors
        }