# Candidate Canonicalization Engine — Architecture

This document reflects the **actual implementation** in the codebase, not the original planned design.

## Compact Overview (One-Page)

```mermaid
flowchart LR
    Config["Config JSON"] --> CC["ConfigCompiler"]
    CC --> Plan["ProjectionPlan"]

    CSV["CSV"] --> CA["CSVAdapter"]
    PDF["PDF"] --> RA["ResumeAdapter"]

    CA -->|"normalized partial"| IR["IdentityResolver"]
    RA -->|"normalized partial"| IR

    CA --> ME["MergeEngine"]
    RA --> ME
    ME --> CR["ConflictResolver"]
    CR --> CAN["Canonical Record"]

    IR --> CAN

    CAN --> ENR["Enrichment: Provenance / Confidence / Audit / Quality"]
    ENR --> VAL1["Pydantic Schema"]
    VAL1 --> PE["ProjectionEngine"]
    Plan --> PE
    PE --> VAL2["ProjectionValidator"]
    Plan --> VAL2
    VAL2 --> OUT["profile.json"]
    VAL1 --> CANOUT["canonical.json"]
```

## Repository Structure

```
eightfold/
├── main.py                          # Typer CLI entry point
├── configs/default.json             # Runtime projection config
├── sample_data/recruiter.csv
├── sample_data/resume.pdf
├── app/
│   ├── services/pipeline.py         # CandidatePipeline orchestrator
│   ├── adapters/                    # CSVAdapter, ResumeAdapter
│   ├── normalizers/                 # email, phone, skills, location, result
│   ├── merger/                      # identity, merge, conflict, provenance, audit
│   ├── confidence/scorer.py         # ConfidenceScorer
│   ├── quality/report.py            # QualityReport
│   ├── canonical/schema.py          # Pydantic Candidate + validate_canonical
│   ├── projection/                  # compiler, validator, projector, models
│   ├── validation/validator.py      # ProjectionValidator
│   └── output/generator.py          # OutputGenerator
└── tests/
```

## Pipeline Steps

| Step | Component | Output |
|------|-----------|--------|
| 1 | `ConfigCompiler.compile` | `ProjectionPlan` or early exit with `config_errors` |
| 2 | `CSVAdapter.extract` | Partial record + `_normalization_report` + `_uncertain_fields` |
| 3 | `ResumeAdapter.extract` | Partial record + `_normalization_report` + `_uncertain_fields` |
| 4 | `IdentityResolver.resolve` | `identity` (score + match_keys) |
| 5 | `IdentityResolver.generate_candidate_id` | `candidate_id` |
| 6 | `MergeEngine.merge` (uses `ConflictResolver`) | Core fields + `conflict_report` + `_merge_decisions` |
| 7 | `NormalizationReport.merge` | `normalization_report` on canonical |
| 8 | `ProvenanceTracker.build` | `provenance` |
| 9 | `ConfidenceScorer.score_profile` | `confidence` + `overall_confidence` |
| 10 | `AuditTrail.generate` | `_audit` |
| 11 | `QualityReport.generate` | `quality_report` |
| 12 | `validate_canonical` | Pydantic `Candidate` (structured error on failure) |
| 13 | `ProjectionEngine.project` | `ProjectionResult` (output + missing_events) |
| 14 | `ProjectionValidator.validate` | validation report (errors/warnings) |
| 15 | `OutputGenerator` | Write JSON files; CLI exit codes |

## Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant CLI as main.py
    participant Pipe as CandidatePipeline
    participant CC as ConfigCompiler
    participant CV as ConfigValidator
    participant CA as CSVAdapter
    participant RA as ResumeAdapter
    participant IR as IdentityResolver
    participant ME as MergeEngine
    participant CR as ConflictResolver
    participant PT as ProvenanceTracker
    participant CS as ConfidenceScorer
    participant AT as AuditTrail
    participant QR as QualityReport
    participant Schema as validate_canonical
    participant PE as ProjectionEngine
    participant PV as ProjectionValidator
    participant OG as OutputGenerator

    User->>CLI: python main.py run --csv --resume --config --output
    CLI->>CLI: validate input paths
    CLI->>Pipe: run(csv_path, resume_path, config_path)

    Pipe->>CC: compile(config_path)
    CC->>CV: validate(config)
    alt config invalid
        CV-->>Pipe: errors
        Pipe-->>CLI: config_errors, canonical=null
        CLI-->>User: exit 1
    end
    CV-->>CC: valid
    CC-->>Pipe: ProjectionPlan

    Pipe->>CA: extract(csv_path)
    CA-->>Pipe: csv_data + _normalization_report
    Pipe->>RA: extract(resume_path)
    RA-->>Pipe: resume_data + _normalization_report

    Pipe->>IR: resolve(csv_data, resume_data)
    IR-->>Pipe: identity
    Pipe->>IR: generate_candidate_id(...)
    IR-->>Pipe: candidate_id

    Pipe->>ME: merge(csv_data, resume_data)
    loop each scalar/collection field
        ME->>CR: resolve_scalar / resolve_collection
        CR-->>ME: decision + optional conflict
    end
    ME-->>Pipe: canonical + conflict_report + _merge_decisions

    Pipe->>Pipe: attach candidate_id, identity, normalization_report
    Pipe->>PT: build(csv, resume, canonical)
    PT-->>Pipe: provenance
    Pipe->>CS: score_profile(canonical, csv, resume)
    CS-->>Pipe: confidence, overall_confidence
    Pipe->>AT: generate(canonical, confidence)
    AT-->>Pipe: _audit
    Pipe->>QR: generate(canonical, confidence)
    QR-->>Pipe: quality_report

    Pipe->>Schema: validate_canonical(canonical)
    alt schema invalid
        Schema-->>Pipe: schema_errors
        Pipe-->>CLI: canonical=null
        CLI-->>User: exit 1
    end
    Schema-->>Pipe: Candidate model

    Pipe->>PE: project(canonical, plan)
    PE-->>Pipe: projected output + missing_events
    Pipe->>PV: validate(output, plan, missing_events, identity)
    PV-->>Pipe: validation report

    Pipe-->>CLI: canonical, projected, validation
    CLI->>OG: write_projected / write_canonical
    CLI->>CLI: print warnings/errors/quality score
    alt validation errors
        CLI-->>User: exit 1
    else success
        CLI-->>User: exit 0
    end
```

## Data Flow

```mermaid
flowchart LR
    subgraph sourceData [Source Records]
        CSVData["csv_data dict"]
        ResumeData["resume_data dict"]
    end

    subgraph mergeData [After Merge]
        MergeDecisions["_merge_decisions internal"]
        ConflictReport["conflict_report"]
    end

    subgraph enriched [Enriched Canonical]
        Prov["provenance"]
        Conf["confidence"]
        Audit["_audit"]
        Qual["quality_report"]
        NormRep["normalization_report"]
    end

    subgraph projected [Projected Output]
        Fields["mapped fields"]
        Meta["_confidence _provenance _quality _audit _conflicts _normalization_report"]
        Valid["_validation optional"]
    end

    CSVData --> MergeEngine2["MergeEngine"]
    ResumeData --> MergeEngine2
    MergeEngine2 --> MergeDecisions
    MergeEngine2 --> ConflictReport
    MergeDecisions --> Prov
    MergeDecisions --> Audit
    ConflictReport --> Conf
    NormRep --> Qual
    Prov --> Conf

    enriched --> ProjectionEngine2["ProjectionEngine"]
    ProjectionEngine2 --> Fields
    ProjectionEngine2 --> Meta
    ProjectionEngine2 --> Valid
```

### Normalization tiers

1. **Adapter extract** — email, phone, location (`csv_adapter.py`, `resume_adapter.py`)
2. **Merge** — skills canonicalization, location re-parse, email/phone detailed candidates (`merge_engine.py`)
3. **Projection** — optional per-field `email`, `E164`, `canonical` (`projector.py`)

### Validation tiers

1. **Config compile** — `ConfigValidator` (blocks pipeline)
2. **Canonical schema** — Pydantic `Candidate` (returns `schema_errors` on failure)
3. **Post-projection** — `ProjectionValidator` (errors/warnings; CLI exit 1 on errors)

## Component Glossary

| Name | Class / file | Description |
|------|--------------|-------------|
| CLI | `main.py` | Typer entry point; validates paths, invokes pipeline, delegates file writes to OutputGenerator |
| CandidatePipeline | `app/services/pipeline.py` | Orchestrates config compile → extract → identity → merge → enrich → schema validate → project → validate |
| CSVAdapter | `app/adapters/csv_adapter.py` | Reads first CSV row via pandas; normalizes email/phone/location |
| ResumeAdapter | `app/adapters/resume_adapter.py` | Extracts PDF text via PyMuPDF; regex-parses fields; normalizes contact data |
| Normalizers | `app/normalizers/` | email, phone (E.164), skills (alias map), location (city/country struct) |
| IdentityResolver | `app/merger/identity_resolver.py` | Scores email/phone/name match; generates deterministic `candidate_id` |
| MergeEngine | `app/merger/merge_engine.py` | Field-level deterministic merge; delegates conflicts to ConflictResolver |
| ConflictResolver | `app/merger/conflict_resolver.py` | Resolves scalar/collection conflicts with explicit policies |
| ProvenanceTracker | `app/merger/provenance.py` | Per-field source history, method, resolution policy, item-level traceability |
| ConfidenceScorer | `app/confidence/scorer.py` | Per-field and overall confidence from weights, bonuses, and penalties |
| QualityReport | `app/quality/report.py` | Completeness, consistency, trust, and composite quality_score |
| AuditTrail | `app/merger/audit.py` | `_audit` block with selected value, candidates, policy, confidence per field |
| ConfigCompiler | `app/projection/compiler.py` | Loads JSON config, validates, compiles into ProjectionPlan |
| ConfigValidator | `app/projection/config_validator.py` | Validates field rules, on_missing, include flags at compile time |
| ProjectionEngine | `app/projection/projector.py` | Maps canonical fields to downstream schema via path resolution and toggles |
| ProjectionValidator | `app/validation/validator.py` | Post-projection required-field, missing-value, and identity warnings |
| validate_canonical | `app/canonical/schema.py` | Pydantic Candidate model validation (non-mutating) |
| OutputGenerator | `app/output/generator.py` | Writes projected and canonical JSON to disk |

## Implementation vs. Planned Design

| Area | Planned / old README | Actual implementation |
|------|----------------------|----------------------|
| Config timing | ConfigCompiler after enrichment | ConfigCompiler runs **first** |
| Normalization | Standalone pipeline stage | **Embedded** in adapters, merge, and projection |
| Conflict resolution | Separate stage after merge | **Sub-component** of MergeEngine |
| Class naming | ProvenanceEngine, ValidationEngine | `ProvenanceTracker`, `ProjectionValidator` |
| Identity gating | Check before merge | Score is advisory; warning only at validation |
| Skills in CSV | Union from both sources | CSVAdapter does **not** extract skills |
| Resume skills | Normalized at extract | Keyword match at extract; `normalize_skills` at **merge** |
| `_merge_decisions` | Projected metadata | Internal only; used by ProvenanceTracker and AuditTrail |

## Known Gaps

- Identity score does not block merge; consider configurable enforcement for safety-critical use cases.
- CSV skills column is not supported; only resume contributes skills today.
- Adapters run sequentially; they could be parallelized for latency.
- `normalize_date` exists in `app/normalizers/date.py` but is not wired into the pipeline.
