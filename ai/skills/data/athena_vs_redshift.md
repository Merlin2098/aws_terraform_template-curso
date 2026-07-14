# Athena vs Redshift Decision Guidance

## When to use

- Choosing a query engine for a new analytics workload over the S3 data lake
- Explaining why this course's labs use Athena exclusively (no Redshift lab)
- Reviewing a proposal to introduce Redshift into a small/lab-scale project

## Core idea

Athena and Redshift solve the same problem — SQL over large datasets — with
opposite cost models: Athena is serverless and billed per query (per byte
scanned), Redshift is a provisioned cluster billed per hour regardless of
query volume. The deciding factor is rarely "which is more powerful" — it's
whether the workload has steady, high-concurrency query traffic (favoring a
standing cluster) or intermittent, unpredictable query traffic (favoring
pay-per-query).

---

## Decision table

| Dimension | Athena | Redshift |
|---|---|---|
| Infrastructure | Serverless — no cluster to manage | Provisioned cluster (or Redshift Serverless, a separate hybrid option) |
| Cost model | Per query, per byte scanned | Per hour the cluster runs, regardless of query volume |
| Latency | Seconds, higher for very large scans | Sub-second to seconds, optimized via cluster-resident data |
| Concurrency | Scales automatically, workgroup limits apply | Fixed by cluster size — sizing is a capacity-planning exercise |
| Data location | Queries data in place in S3 (no load step) | Data is typically loaded/copied into the cluster (`COPY` from S3) |
| Best fit | Intermittent, ad-hoc, or unpredictable query patterns | Steady, high-concurrency BI/dashboard workloads querying the same datasets repeatedly |
| Setup complexity | Point at S3 + Glue Catalog, query immediately | Provision cluster, design distribution/sort keys, load data |

---

## When Athena wins

- Query traffic is intermittent (a few queries per hour, ad-hoc exploration) — matches every lab in this course.
- The dataset already lives in S3 as the data lake's source of truth — no separate load/ETL step is needed.
- There's no dedicated team to size, tune, and pay for a standing cluster.
- Cost must scale to zero when nobody is querying — Athena has no idle cost; a Redshift cluster does.

## When Redshift wins

- Dozens of analysts run dashboards continuously against the same tables — spreading fixed cluster cost across high, steady query volume becomes cheaper than paying per byte scanned on every refresh.
- Query patterns benefit from Redshift-specific optimizations (distribution keys, sort keys, materialized views) that outperform Athena on repeated, complex joins.
- The organization already operates Redshift for other workloads, and marginal cost of one more dataset is low.

---

## Cost for a course lab

A Redshift cluster (even the smallest node type) is a **standing cost** —
it bills every hour it exists, independent of whether a query ever runs
against it, the same trap described for RDS in
`ai/skills/aws/rds_overview.md`. Athena has **no idle cost** — a workgroup
with zero queries costs nothing beyond S3 storage. For this reason, this
course's Session 6 uses Athena exclusively; a Redshift lab would require
remembering to tear the cluster down between sessions or accepting a
continuous bill for the duration of the course.

---

## Migration path

Projects often start on Athena (low commitment, no infrastructure) and adopt
Redshift later once query volume and concurrency justify it — not the
reverse. The tables and partition structure in
`ai/skills/aws/glue_crawler_catalog.md` and `ai/skills/aws/s3_data_lake.md`
carry over conceptually: Redshift Spectrum can even query the same S3 data
directly without a full `COPY`, as an intermediate step before fully loading
data into cluster-native storage.

---

## Avoid

- Standing up a Redshift cluster for a course lab or low-traffic prototype — the fixed hourly cost outweighs the benefit at this scale
- Choosing Redshift because it "sounds more production-grade" without a concurrency/latency requirement that actually needs it
- Comparing the two purely on raw query performance without factoring in the idle-cost difference
- Leaving a Redshift cluster running between sessions in a learning environment

## See also

- `ai/skills/data/athena_patterns.md` — the query patterns this course actually uses
- `ai/skills/aws/rds_overview.md` — the same standing-cost trade-off applied to relational OLTP workloads
- `ai/skills/aws/s3_data_lake.md` — the data lake structure both engines would query
- `ai/skills/data/etl_patterns.md` — the bronze/silver/gold flow that feeds either engine
