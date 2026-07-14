# AWS Glue Job Pattern

## When to use

- Batch ETL pipelines transforming data already cataloged (see `ai/skills/aws/glue_crawler_catalog.md`)
- S3 → S3 transformations (bronze → silver → gold)
- Structured data processing (Parquet, CSV, JSON) too large or too heavy for Lambda

## Core idea

A Glue **job** is the transform step — it reads, transforms, and writes data.
Discovering schema and registering tables in the Data Catalog is a separate
concern handled by a **crawler** (`ai/skills/aws/glue_crawler_catalog.md`).
Keep these responsibilities distinct: a job should read from catalog tables
the crawler already populated, not re-infer schema itself in production.

---

## Architecture

```
S3 (bronze) → Glue Crawler → Data Catalog (schema/partitions)
                                     ↓
                             Glue Job (transform)
                                     ↓
                        S3 (silver/gold) → Crawler → Data Catalog
```

---

## Terraform — Glue job

```hcl
resource "aws_s3_object" "etl_script" {
  bucket = aws_s3_bucket.scripts.id
  key    = "glue/bronze_to_silver.py"
  source = "${path.module}/scripts/bronze_to_silver.py"
  etag   = filemd5("${path.module}/scripts/bronze_to_silver.py")
}

resource "aws_glue_job" "bronze_to_silver" {
  name              = "${local.name_prefix}-bronze-to-silver"
  role_arn          = aws_iam_role.glue_job.arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30  # minutes

  command {
    script_location = "s3://${aws_s3_bucket.scripts.id}/${aws_s3_object.etl_script.key}"
    python_version   = "3"
  }

  default_arguments = {
    "--job-bookmark-option"       = "job-bookmark-enable"
    "--enable-metrics"            = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                   = "s3://${aws_s3_bucket.scripts.id}/tmp/"
    "--source_database"           = aws_glue_catalog_database.bronze.name
    "--target_bucket"             = aws_s3_bucket.data_lake.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "glue_job" {
  name              = "/aws-glue/jobs/${local.name_prefix}-bronze-to-silver"
  retention_in_days = 14  # explicit — never omit (SPEC-009)
  tags              = local.common_tags
}
```

Always set `--TempDir` explicitly — Glue jobs fail or silently use an
unmanaged location if it is omitted. `job-bookmark-option = job-bookmark-enable`
makes reruns process only new data since the last successful run, avoiding
duplicate processing on retry.

---

## PySpark vs Python shell

| | Glue ETL (Spark) | Python shell |
|---|---|---|
| When to use | Large datasets, distributed transforms, joins across large tables | Lightweight scripts, small datasets, simple file manipulation |
| Worker type | `G.1X` / `G.2X` (Spark workers) | `Standard` (1 or 0.0625 DPU) |
| Cost model | Billed per DPU-hour, minimum 10 DPU-minutes | Billed per DPU-hour, much lower floor |
| Typical use in this course | Bronze → silver transforms over the full data lake | Small config/metadata tasks, one-off scripts |

For course labs processing modest sample datasets, start with Python shell
if the transform is simple; move to Spark (`G.1X`) only when the dataset size
or transform complexity justifies distributed processing.

---

## Job entrypoint structure

```python
import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from pyspark.context import SparkContext

args = getResolvedOptions(sys.argv, ["JOB_NAME", "source_database", "target_bucket"])
sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

# Read from the catalog table the crawler already registered — do not
# re-infer schema at job runtime.
df = glue_context.create_dynamic_frame.from_catalog(
    database=args["source_database"],
    table_name="invoices",
).toDF()

transformed = df.dropDuplicates(["invoice_id"]).filter(df.total_amount.isNotNull())

transformed.write.mode("overwrite").partitionBy("partition_date").parquet(
    f"s3://{args['target_bucket']}/silver/invoices/"
)
```

Separate SQL-shaped logic into external `.sql` files where the transform is
primarily filtering/joining — see `ai/skills/sql/sql_workflow_guidance.md`.
Keep only orchestration and I/O in the Python entrypoint.

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| Job fails with an out-of-memory error | Wrong worker type/count for the data volume, or a skewed join | Increase `number_of_workers` or switch to `G.2X`; check for partition skew |
| Reprocesses the same data on every run | Job bookmarks not enabled | Set `--job-bookmark-option = job-bookmark-enable` |
| `TempDir not defined` or jobs write to an unexpected location | `--TempDir` omitted from `default_arguments` | Always set `--TempDir` explicitly to a project-owned S3 prefix |
| `AccessDenied` reading source data or writing output | Glue job role missing S3 permissions | Attach a scoped IAM policy per `ai/skills/aws/iam_policies.md` |
| No logs visible after a failed run | Missing or misconfigured `aws_cloudwatch_log_group` | Declare the log group explicitly with `retention_in_days` set (SPEC-009) |

---

## Avoid

- Re-inferring schema inside the job when a crawler-managed catalog table already exists
- Embedding SQL transformation logic as long inline strings in Python
- Omitting `--TempDir` or job bookmarks
- Relying on Glue's autogenerated log group instead of declaring one explicitly
- Using Spark workers (`G.1X`/`G.2X`) for a trivial transform that a Python shell job would handle at a fraction of the cost

## See also

- `ai/skills/aws/glue_crawler_catalog.md` — schema discovery and catalog registration that feeds this job
- `ai/skills/aws/s3_data_lake.md` — bronze/silver/gold layout this job reads from and writes to
- `ai/skills/data/etl_patterns.md` — bronze/silver/gold transformation conventions
- `ai/skills/terraform/terraform_governance.md` — mandatory tags, log retention, and per-DPU-hour cost awareness
