# AWS Lake Formation Intro Pattern

## When to use

- Introducing centralized, fine-grained governance over a data lake's Glue Catalog tables
- Explaining why IAM alone is insufficient once multiple teams/roles query the same catalog
- Reviewing a "why can't this role query this table" issue that isn't an IAM problem

## Core idea

Lake Formation adds a second, finer-grained permission layer **on top of**
IAM, scoped to database/table/column level access on the Glue Data Catalog —
IAM alone can only grant or deny access to the catalog API and S3 objects as
a whole, not "this role may see columns A and B of this table but not C."
The most common early confusion is not realizing an AWS account defaults to
**IAM-only mode**: without an explicit Lake Formation permission grant (in
LF-managed mode), IAM permissions alone govern access exactly as they did
before Lake Formation existed.

---

## The two-layer mental model

```
IAM                          →  Can this principal call glue:GetTable / s3:GetObject at all?
Lake Formation permissions   →  Given IAM allows it, which databases/tables/columns specifically?
```

Both layers must permit access. Lake Formation does not replace IAM — it
narrows what an already-IAM-permitted principal can see within the catalog.

---

## Registering an S3 location

Before Lake Formation can govern a data lake location, it must be registered:

```hcl
resource "aws_lakeformation_resource" "data_lake" {
  arn = aws_s3_bucket.data_lake.arn
}
```

This tells Lake Formation to manage permissions for objects under this
bucket, rather than deferring entirely to IAM/S3 bucket policies.

---

## Data lake administrator

Lake Formation requires at least one designated administrator — the
identity allowed to grant/revoke Lake Formation permissions to others:

```hcl
resource "aws_lakeformation_data_lake_settings" "this" {
  admins = [aws_iam_role.data_engineer.arn]
}
```

Without this, no one (not even an account admin) can manage Lake Formation
permissions through the console or API — a common first-setup blocker.

---

## Granting table-level permissions

```hcl
resource "aws_lakeformation_permissions" "analyst_select" {
  principal   = aws_iam_role.analyst.arn
  permissions = ["SELECT"]

  table {
    database_name = aws_glue_catalog_database.silver.name
    name          = "invoices"
  }
}
```

## Column-level permissions

```hcl
resource "aws_lakeformation_permissions" "analyst_limited_columns" {
  principal   = aws_iam_role.analyst.arn
  permissions = ["SELECT"]

  table_with_columns {
    database_name = aws_glue_catalog_database.silver.name
    name          = "invoices"
    column_names  = ["invoice_id", "invoice_date", "total_amount"]
    # omits any PII column, e.g. customer_email
  }
}
```

Column-level grants are the concrete capability IAM alone cannot express —
IAM can grant or deny `glue:GetTable`, but not "only these columns of this
table."

---

## Interaction with existing IAM policies

Once a resource location is registered with Lake Formation (as above), Athena
and Glue access to that location is evaluated through Lake Formation
permissions in addition to IAM. A role with broad `s3:GetObject`/`glue:*` IAM
permissions but no Lake Formation grant will be denied at the Lake Formation
layer — this is a deliberate governance boundary, not a bug.

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| A role with seemingly correct IAM permissions still can't query a table via Athena | No Lake Formation permission granted, or the location isn't registered as expected | Grant `SELECT` via `aws_lakeformation_permissions`, confirm registration via `aws_lakeformation_resource` |
| "No data lake administrator" errors when managing permissions | `aws_lakeformation_data_lake_settings.admins` never set | Designate at least one administrator role/user |
| Permissions behave exactly as plain IAM/S3, ignoring Lake Formation grants | Account still in IAM-only default mode — the S3 location was never registered | Register the S3 location with `aws_lakeformation_resource` |
| A user can see a table but not the sensitive columns they expect to be hidden | Column-level grant not applied — table-level `SELECT` alone grants all columns | Use `table_with_columns` with an explicit `column_names` allowlist |

---

## Avoid

- Assuming Lake Formation is active as soon as it appears in the console — it only governs registered locations
- Granting `SELECT` on entire tables when column-level segregation of sensitive fields is the actual requirement
- Skipping the data lake administrator designation and then being unable to manage permissions
- Treating Lake Formation as a replacement for IAM least privilege — it is an additional, narrower layer

## See also

- `ai/skills/aws/glue_crawler_catalog.md` — the catalog tables Lake Formation permissions apply to
- `ai/skills/aws/iam_policies.md` — the IAM layer that must independently permit access first
- `ai/skills/aws/s3_data_lake.md` — the S3 locations registered with Lake Formation
