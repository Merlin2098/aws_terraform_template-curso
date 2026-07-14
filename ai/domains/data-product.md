# Domain: Data Product

## Purpose

Guidance for building and maintaining data pipelines that ingest, transform, validate,
and serve data. This domain covers the full lifecycle of a data product: from raw
ingestion (Bronze) through validated transformation (Silver) to analytical serving (Gold).
It is technology-agnostic at the pattern level but assumes AWS as the execution environment.

---

## Scope

| In scope | Out of scope |
|---|---|
| ETL pipeline design (Bronze / Silver / Gold) | AWS service configuration (see `ai/domains/aws.md`) |
| Data contracts and schema enforcement | Terraform infrastructure for pipelines (see `ai/domains/terraform.md`) |
| Data quality checks (Python, SQL, AWS) | Python job implementation patterns (see `ai/domains/python.md`) |
| SQL transformations and workflow | Machine learning model training |
| Athena query patterns and cost control | Frontend dashboards (see `ai/domains/frontend.md`) |
| OCR normalisation and LLM extraction stages | |

---

## Skills

| Skill | File | Description |
|---|---|---|
| ETL patterns | `ai/skills/data/etl_patterns.md` | Bronze/Silver/Gold layers, transformations, OCR normalisation with prompt versioning |
| Data contracts | `ai/skills/data/data_contracts.md` | Data validation and schema enforcement |
| Data quality | `ai/skills/data/data_quality_guidance.md` | Deterministic data quality checks for Python, SQL, and AWS workflows |
| Athena patterns | `ai/skills/data/athena_patterns.md` | Query lifecycle, result pagination, partition pruning, and workgroup cost guardrails |
| Athena vs Redshift | `ai/skills/data/athena_vs_redshift.md` | Decision guidance for serverless query vs provisioned warehouse |
| SQL workflow | `ai/skills/sql/sql_workflow_guidance.md` | Maintainable SQL file organisation and transformation workflow guidance |

---

## Policies

No domain-specific policies beyond the global set. See [`ai/policies/global.md`](../policies/global.md).

Key global policies that apply most often in this domain:

- **Configuration Over Hardcoding** — S3 paths, table names, and thresholds must come from config, not from inline literals.
- **Security By Default** — data at rest must be encrypted; IAM roles must be scoped to specific buckets and prefixes.

---

## References

- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Related domains: `ai/domains/aws.md`, `ai/domains/python.md`, `ai/domains/terraform.md`
- Spec that governs domain structure: `specs/rework/SPEC-FW-003.md`
