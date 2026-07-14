# DynamoDB Modeling Pattern

## When to use

- Storing high-throughput, key-based access data (sessions, events, lookups)
- Deciding between DynamoDB and a relational database (see `ai/skills/aws/rds_overview.md`)
- Designing a table's primary key before writing any code
- Reviewing Python code that reads/writes DynamoDB items

## Core idea

Model DynamoDB tables around **access patterns**, not entities — the opposite
of relational design. Decide every query the application needs to run first,
then design the partition key (PK) and sort key (SK) so each query is a
single `Query` call. The two most common production failures are: scanning
instead of querying (slow, expensive, scales with table size), and a
partition key with low cardinality that creates a "hot partition" (throttling
concentrated on one physical partition).

---

## Partition key and sort key

| Key | Role |
|---|---|
| Partition key (PK) | Determines which physical partition stores the item. Must have high cardinality to spread load. |
| Sort key (SK, optional) | Orders items within a partition and enables range queries (`begins_with`, `between`). |

A table with both PK and SK supports one-to-many relationships without a
join: all items sharing a PK are retrievable in one `Query`, sorted by SK.

```
PK                  SK
STUDENT#01          PROFILE
STUDENT#01          ENROLLMENT#2026-01
STUDENT#01          ENROLLMENT#2026-02
```

A single `Query` with `PK = "STUDENT#01"` returns the profile and every
enrollment — no join required.

---

## Single-table basics

DynamoDB has no joins and charges per request, so a common pattern is storing
multiple entity types in one table, distinguished by PK/SK prefixes (as
above: `STUDENT#`, `ENROLLMENT#`). This is an advanced pattern — for a course
lab, a simple one-entity-per-table design is appropriate and easier to
reason about. Introduce single-table design only when access patterns
actually require joining across entity types in one query.

---

## boto3 CRUD

```python
import boto3
from botocore.exceptions import ClientError

table = boto3.resource("dynamodb", region_name="us-east-1").Table("course-students")

def put_student(student_id: str, name: str, email: str) -> None:
    table.put_item(Item={"student_id": student_id, "name": name, "email": email})

def get_student(student_id: str) -> dict | None:
    response = table.get_item(Key={"student_id": student_id})
    return response.get("Item")

def query_enrollments(student_id: str) -> list[dict]:
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
        ExpressionAttributeValues={
            ":pk": f"STUDENT#{student_id}",
            ":prefix": "ENROLLMENT#",
        },
    )
    return response["Items"]

def update_email(student_id: str, new_email: str) -> None:
    table.update_item(
        Key={"student_id": student_id},
        UpdateExpression="SET email = :email",
        ConditionExpression="attribute_exists(student_id)",
        ExpressionAttributeValues={":email": new_email},
    )
```

`ConditionExpression="attribute_exists(student_id)"` prevents `update_item`
from silently creating a new item if the key does not already exist —
`update_item` upserts by default.

---

## Terraform — table definition

```hcl
resource "aws_dynamodb_table" "students" {
  name         = "${local.name_prefix}-students"
  billing_mode = "PAY_PER_REQUEST"  # no capacity planning needed for a lab
  hash_key     = "student_id"

  attribute {
    name = "student_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false  # off by default in dev/sandbox — enable explicitly if required
  }

  tags = local.common_tags
}

output "table_name" {
  value       = aws_dynamodb_table.students.name
  description = "DynamoDB table name for application configuration."
}

output "table_arn" {
  value       = aws_dynamodb_table.students.arn
  description = "DynamoDB table ARN for IAM policy scoping."
}
```

Use `PAY_PER_REQUEST` (on-demand) billing for course labs — it removes
capacity-unit planning and its cost model matches intermittent lab traffic.
Switch to `PROVISIONED` only when traffic is steady and predictable enough to
make reserved capacity cheaper.

For a composite key (PK + SK), add a `range_key` and a second `attribute`
block:

```hcl
resource "aws_dynamodb_table" "student_records" {
  name         = "${local.name_prefix}-student-records"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  tags = local.common_tags
}
```

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `scan` is slow and expensive as the table grows | Query pattern wasn't known at design time, forcing a full-table scan | Redesign PK/SK (or add a GSI) so the access pattern becomes a `Query` |
| Throttling concentrated on specific requests | Low-cardinality partition key (e.g. a fixed `"ALL"` value) creates a hot partition | Choose a partition key with high cardinality (student ID, not a constant) |
| `update_item` creates unexpected new items | No `ConditionExpression` guarding against upsert | Add `ConditionExpression="attribute_exists(pk)"` when the intent is update-only |
| Need to query by an attribute that isn't the PK/SK | Access pattern not modeled into the key design | Add a Global Secondary Index (GSI) — out of scope for a first lab, but the standard fix |

---

## Avoid

- Using `scan` in application code paths that run repeatedly — reserve it for one-off admin/debug queries
- A partition key with only a handful of distinct values (e.g. status flags) — guarantees a hot partition
- Designing the table before listing the access patterns the application needs
- `PROVISIONED` billing mode for unpredictable lab traffic — `PAY_PER_REQUEST` avoids both throttling and idle capacity cost
- Skipping `ConditionExpression` on updates that must not silently create new items

## See also

- `ai/skills/aws/rds_overview.md` — when a relational database is the better fit
- `ai/skills/aws/iam_policies.md` — least-privilege policy scoped to `dynamodb:*` actions and the table ARN
- `ai/skills/terraform/terraform_governance.md` — mandatory tags and budget awareness for DynamoDB read/write costs
- `ai/skills/python/python_project_guidance.md` — module structure for a `clients/dynamodb.py`-style wrapper
