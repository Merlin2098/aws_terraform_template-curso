# S3 Data Lake Pattern

## When to use

- Storing raw and processed data for analytics
- Designing the bronze/silver/gold layer structure for a pipeline
- Configuring lifecycle, versioning, and bucket policies for a data lake bucket

## Core idea

Use S3 as the central storage layer, organized into layers by processing
stage. The two most common production mistakes are: applying security
controls after the bucket already holds data (retrofitted security is
Policy 004's exact anti-pattern), and skipping lifecycle rules until storage
cost becomes visible on a bill.

---

## Layer structure

```
s3://<bucket>/bronze/<dataset>/<partition_date>/...   # raw ingestion
s3://<bucket>/silver/<dataset>/<partition_date>/...   # validated, cleaned
s3://<bucket>/gold/<dataset>/<partition_date>/...     # business-ready, aggregated
```

Use Parquet for silver/gold (columnar, compressed, Athena-friendly). Bronze
may keep the source format (CSV, JSON, TIF) since it mirrors the raw input.
Partition by date or a natural business key (`partition_date=YYYY-MM-DD`) —
see `ai/skills/data/athena_patterns.md` for how this partition layout is
queried efficiently.

---

## Terraform — bucket with security defaults

```hcl
resource "aws_s3_bucket" "data_lake" {
  bucket        = "${local.name_prefix}-data-lake"
  force_destroy = true  # required for clean `terraform destroy` in dev/sandbox
  tags          = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn  # or omit for SSE-S3 in a low-stakes lab
    }
  }
}
```

`force_destroy = true` lets `terraform destroy` remove a non-empty bucket —
appropriate for dev/sandbox, never for a bucket holding production data.

---

## Bucket policy — deny non-TLS requests

```hcl
data "aws_iam_policy_document" "deny_insecure_transport" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.data_lake.arn,
      "${aws_s3_bucket.data_lake.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  policy = data.aws_iam_policy_document.deny_insecure_transport.json
}
```

---

## Lifecycle policy — transition and expire by layer

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "bronze-expire"
    status = "Enabled"
    filter { prefix = "bronze/" }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = 180  # raw data has limited retention value once processed to silver/gold
    }
  }

  rule {
    id     = "gold-archive"
    status = "Enabled"
    filter { prefix = "gold/" }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}
```

Scope lifecycle rules per layer prefix — bronze data typically has a short
useful life once promoted, while gold data is worth archiving rather than
deleting.

---

## Versioning

```hcl
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = var.enable_artifact_bucket_versioning ? "Enabled" : "Disabled"
  }
}
```

**Educational exception (course lab):** SPEC-009 disables S3 versioning by
default (see `ai/skills/terraform/terraform_governance.md`, "Versioning
policy") because it causes hidden storage cost and complicates
`terraform destroy` in disposable environments. For the Session 3
data-lake lab, set `enable_artifact_bucket_versioning = true` deliberately
to demonstrate object versioning and recovery — this is a lab-scoped
override with explicit pedagogical justification, not a change to the
production default. Before `terraform destroy`, every object version must
be removed first (`aws s3api delete-objects` per version, or empty the
bucket via the console) — a plain `force_destroy = true` does not always
clear all historical versions in one pass.

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `terraform destroy` fails: bucket not empty | Versioning was enabled and old versions remain | Delete all object versions before destroy, or confirm `force_destroy` behavior for the provider version in use |
| Athena queries scan far more data than expected | Flat structure without date/domain partitioning | Adopt the `bronze/<dataset>/<partition_date>/` layout and partition on it |
| Public access accidentally exposed | `aws_s3_bucket_public_access_block` omitted or a bucket policy grants `Principal: "*"` without a condition | Always attach the public access block; scope bucket policies with explicit conditions |
| Objects readable over plain HTTP | No bucket policy denying insecure transport | Attach the `DenyInsecureTransport` policy statement |

---

## Avoid

- Flat file structure with no bronze/silver/gold separation
- Mixing raw and processed data in the same prefix
- Enabling versioning by default outside a documented lab exception (see above)
- Public bucket policies or missing `aws_s3_bucket_public_access_block`
- Applying security configuration after data already exists in the bucket

## See also

- `ai/skills/data/athena_patterns.md` — querying this partition layout efficiently
- `ai/skills/aws/glue_crawler_catalog.md` — cataloging this bucket's structure into Glue
- `ai/skills/terraform/terraform_governance.md` — versioning policy, tagging, and budget governance
- `ai/skills/aws/iam_policies.md` — least-privilege access to this bucket from Lambda/Glue roles
