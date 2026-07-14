# Glue Crawler + Data Catalog Pattern

## When to use

- Registering schema and partitions for data in S3 so Athena and Glue jobs can query it
- Keeping the Data Catalog in sync after a pipeline writes new partitions
- Complementing a Glue job (`ai/skills/aws/glue_jobs.md`), which transforms data but does not catalog it

## Core idea

A crawler infers schema and partition structure from data in S3 and
registers it as tables in the Glue Data Catalog — the shared metadata store
that both Glue jobs and Athena read from. The two failure modes that cause
the most confusion are: over-crawling (running the crawler on every job
execution, which is slow and can flip-flop inferred types), and schema
drift (new data doesn't match the table definition the crawler registered
earlier, breaking downstream Athena queries silently).

---

## Catalog database

```hcl
resource "aws_glue_catalog_database" "bronze" {
  name = "${local.name_prefix}_bronze"
  tags = local.common_tags
}

resource "aws_glue_catalog_database" "silver" {
  name = "${local.name_prefix}_silver"
  tags = local.common_tags
}
```

Use one database per data-lake layer (bronze/silver/gold) rather than one
database for the whole lake — it keeps table names unambiguous and mirrors
the S3 prefix structure from `ai/skills/aws/s3_data_lake.md`.

---

## Crawler

```hcl
resource "aws_glue_crawler" "silver_invoices" {
  name          = "${local.name_prefix}-silver-invoices-crawler"
  role          = aws_iam_role.glue_crawler.arn
  database_name = aws_glue_catalog_database.silver.name

  s3_target {
    path = "s3://${aws_s3_bucket.data_lake.id}/silver/invoices/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"  # never silently delete tables on a missing partition
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })

  tags = local.common_tags
}
```

`delete_behavior = "LOG"` prevents the crawler from dropping a table
definition just because a partition is temporarily missing (e.g. a job
hasn't run yet for today's date) — it logs the discrepancy instead of
deleting catalog metadata.

---

## Scheduling the crawler

Run the crawler on a schedule (via EventBridge, not on every job execution)
or trigger it explicitly after a Glue job completes writing new partitions:

```hcl
resource "aws_glue_trigger" "crawl_after_job" {
  name = "${local.name_prefix}-crawl-after-etl"
  type = "CONDITIONAL"

  predicate {
    conditions {
      job_name = aws_glue_job.bronze_to_silver.name
      state    = "SUCCEEDED"
    }
  }

  actions {
    crawler_name = aws_glue_crawler.silver_invoices.name
  }

  tags = local.common_tags
}
```

This is more reliable than crawling on a fixed schedule when job completion
time is variable — the crawler only runs after new data actually lands.

---

## Partitions — prefer projection over repeated crawling

For a well-known, predictable partition scheme (date-based), configure
partition projection on the catalog table instead of re-crawling to discover
new partitions — see `ai/skills/data/athena_patterns.md` for the full
`aws_glue_catalog_table` projection example. Partition projection avoids
both the crawler run cost and the metadata-scan cost `MSCK REPAIR TABLE`
incurs.

Use a crawler when the schema itself may evolve (new columns) or partition
values are unpredictable; use projection when the partition pattern
(`partition_date=YYYY-MM-DD`) is fixed and schema is stable.

---

## Crawler IAM role

```hcl
data "aws_iam_policy_document" "glue_crawler_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_crawler" {
  name               = "${local.name_prefix}-glue-crawler"
  assume_role_policy = data.aws_iam_policy_document.glue_crawler_trust.json
  tags               = local.common_tags
}
```

Attach `glue:*` catalog actions scoped to the specific database ARN and
`s3:GetObject`/`s3:ListBucket` scoped to the target prefix — not
`AWSGlueServiceRole` with unrestricted S3 access.

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| Athena query fails with "table not found" after a schema change | Crawler hasn't re-run since new columns appeared | Re-run the crawler, or trigger it via `aws_glue_trigger` after the writing job succeeds |
| Table silently disappears | `delete_behavior` defaulted to deleting tables for missing partitions | Set `schema_change_policy.delete_behavior = "LOG"` |
| Inferred column types keep flip-flopping between runs | Crawler re-inferring on inconsistent sample data (mixed types in early rows) | Enforce a stricter schema at write time (see `ai/skills/data/data_contracts.md`) instead of relying on inference |
| Crawler costs add up | Running on every job execution / fixed short schedule instead of triggered-on-completion or projection | Use `aws_glue_trigger` on job success, or switch to partition projection for predictable partition schemes |

---

## Avoid

- Running the crawler on a fixed short schedule when a conditional trigger (after job success) is more accurate and cheaper
- Using `delete_behavior = "DELETE_FROM_DATABASE"` in a course/lab context — a temporarily missing partition should not delete catalog metadata
- Re-crawling on every job execution as a substitute for partition projection when the partition scheme is predictable
- One shared database for the entire data lake instead of one per layer

## See also

- `ai/skills/aws/glue_jobs.md` — the transform step that reads from tables this crawler catalogs
- `ai/skills/data/athena_patterns.md` — partition projection as an alternative to repeated crawling
- `ai/skills/aws/s3_data_lake.md` — the S3 layout this crawler targets
- `ai/skills/aws/lake_formation_intro.md` — governance permissions layered on top of these catalog tables
