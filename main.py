import json
from pathlib import Path
from typing import Optional

import typer

from app.services.pipeline import CandidatePipeline

app = typer.Typer(
    help="Candidate Canonization Engine — merge recruiter CSV and resume PDF into a canonical profile.",
)


def _validate_input_path(path: str, label: str) -> Path:
    resolved = Path(path)
    if not resolved.exists():
        raise typer.BadParameter(f"{label} not found: {path}")
    return resolved


@app.command()
def run(
    csv: str = typer.Option(
        "sample_data/recruiter.csv",
        "--csv",
        help="Path to recruiter CSV file",
    ),
    resume: str = typer.Option(
        "sample_data/resume.pdf",
        "--resume",
        help="Path to resume PDF file",
    ),
    config: str = typer.Option(
        "configs/default.json",
        "--config",
        help="Path to projection config JSON",
    ),
    output: str = typer.Option(
        "output/profile.json",
        "--output",
        help="Path for projected output JSON",
    ),
    canonical_output: Optional[str] = typer.Option(
        None,
        "--canonical-output",
        help="Optional path to write the full canonical record",
    ),
):
    
    _validate_input_path(csv, "CSV file")
    _validate_input_path(resume, "Resume file")
    _validate_input_path(config, "Config file")

    typer.echo("Running Candidate Transformer Pipeline...")
    typer.echo(f"  CSV:    {csv}")
    typer.echo(f"  Resume: {resume}")
    typer.echo(f"  Config: {config}")

    result = CandidatePipeline().run(
        csv_path=csv,
        resume_path=resume,
        config_path=config,
    )

    if result["warnings"]:
        typer.echo("\nValidation Warnings:")
        for warning in result["warnings"]:
            typer.echo(f"  - {warning}")

    if result["errors"]:
        typer.echo("\nValidation Errors:")
        for error in result["errors"]:
            typer.echo(f"  - {error}")
        raise typer.Exit(code=1)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result["projected"], f, indent=4)

    typer.echo(f"\nProjected output saved to {output_path}")

    if canonical_output:
        canonical_path = Path(canonical_output)
        canonical_path.parent.mkdir(parents=True, exist_ok=True)
        with open(canonical_path, "w", encoding="utf-8") as f:
            json.dump(result["canonical"], f, indent=4, default=str)
        typer.echo(f"Canonical record saved to {canonical_path}")

    quality = result["canonical"].get("quality_report", {})
    typer.echo(
        f"\nQuality score: {quality.get('quality_score', 'n/a')} | "
        f"Overall confidence: {result['canonical'].get('overall_confidence', 'n/a')}"
    )


def main():
    app()


if __name__ == "__main__":
    main()
