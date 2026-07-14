# Amazon RDS Overview Pattern

## When to use

- Deciding between a relational database and DynamoDB (see `ai/skills/aws/dynamodb_modeling.md`)
- Standing up a managed relational database for a lab or demo
- Reviewing an RDS instance for cost and destroyability before `terraform apply`

## Core idea

RDS is a managed relational database, not a serverless service — an instance
runs (and bills) continuously whether or not it is queried, and it lives
inside a VPC with its own networking and security group. In a course
sandbox, the two failure modes that generate surprise bills or blocked
`terraform destroy` runs are: leaving an instance running between sessions,
and a final snapshot silently blocking teardown.

---

## SQL vs NoSQL — when relational wins

| Signal | Choose RDS (relational) | Choose DynamoDB |
|---|---|---|
| Query shape | Ad-hoc queries, joins across entities, aggregations | Known, fixed access patterns by key |
| Schema | Structured, relationships enforced by foreign keys | Flexible, access-pattern-driven |
| Transactions | Multi-table ACID transactions | Single-item or limited multi-item transactions |
| Scale pattern | Vertical scaling, predictable load | Horizontal scaling, spiky/unpredictable load |
| Reporting/analytics | SQL joins and aggregate queries are natural | Requires denormalization or export to Athena/Redshift |

For this course: use RDS when the lab needs relational integrity or ad-hoc
SQL querying; use DynamoDB when the access pattern is a small set of known
key lookups (see `ai/skills/aws/dynamodb_modeling.md`).

---

## Engine and instance basics

| Choice | Course-sandbox default | Notes |
|---|---|---|
| Engine | PostgreSQL | Widely used, free-tier eligible, matches most course SQL material |
| Instance class | `db.t3.micro` or `db.t4g.micro` | Smallest burstable class — sufficient for a lab, not for production load |
| Multi-AZ | Disabled | Doubles cost; unnecessary for a non-production lab |
| Storage | 20 GB `gp3`, no autoscaling | Minimum viable size for a lab dataset |
| Public accessibility | **Disabled** | Never expose an RDS instance directly to the internet (Policy 004 — Security By Default) |

---

## Terraform — minimal destroyable instance

```hcl
resource "aws_db_subnet_group" "lab" {
  name       = "${local.name_prefix}-db-subnets"
  subnet_ids = var.private_subnet_ids
  tags       = local.common_tags
}

resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds-sg"
  description = "Allow Postgres access from application security group only"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]  # never 0.0.0.0/0
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_db_instance" "lab" {
  identifier     = "${local.name_prefix}-db"
  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  storage_type      = "gp3"

  db_name  = var.database_name
  username = var.master_username
  password = var.master_password  # from a variable sourced via env var, never hardcoded

  db_subnet_group_name   = aws_db_subnet_group.lab.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  multi_az            = false
  skip_final_snapshot  = true   # required for clean `terraform destroy` in a lab
  deletion_protection  = false  # required for clean `terraform destroy` in a lab
  backup_retention_period = 0   # no automated backups needed for ephemeral lab data

  tags = local.common_tags
}

output "db_endpoint" {
  value       = aws_db_instance.lab.endpoint
  description = "RDS connection endpoint (host:port)."
}

output "db_arn" {
  value       = aws_db_instance.lab.arn
  description = "RDS instance ARN for IAM policy scoping and monitoring."
}
```

`skip_final_snapshot = true` and `deletion_protection = false` are what let
`terraform destroy` complete without manual console intervention. Both
default to safer production values (`false` and `true` respectively) if
omitted — a course lab must set them explicitly, or teardown will fail or
leave an unmanaged snapshot behind.

---

## Cost and destroyability

RDS is the single highest cost-surprise risk in this course: unlike Lambda,
DynamoDB on-demand, or Athena, an RDS instance bills **continuously** while
it exists, regardless of query volume. Concrete guidance:

- Run `terraform destroy` (or at minimum stop the instance) between sessions
  if the course spans multiple days.
- Never enable Multi-AZ in a lab — it silently doubles the hourly cost.
- Track RDS under the per-service cost awareness table in
  `ai/skills/terraform/terraform_governance.md`.

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `terraform destroy` fails or hangs | `deletion_protection = true` (the AWS default when omitted) | Set `deletion_protection = false` explicitly before destroying |
| Unexpected final snapshot left behind | `skip_final_snapshot` omitted or `false` | Set `skip_final_snapshot = true` for lab/sandbox instances |
| Can't connect from a local machine | `publicly_accessible = false` (correct) but no bastion/VPN/SSM tunnel configured | Connect via an EC2 instance, SSM port forwarding, or a bastion inside the VPC — never flip to public |
| Password rejected by Terraform provider | Password hardcoded or committed to source | Source `master_password` from an environment variable or `.tfvars` excluded from git (Policy 003) |
| Bill higher than expected between sessions | Instance left running with Multi-AZ enabled or over-provisioned storage | Use `db.t3.micro`, `multi_az = false`, and destroy/stop between sessions |

---

## Avoid

- `publicly_accessible = true` — an internet-facing database violates Policy 004 (Security By Default)
- Security group ingress from `0.0.0.0/0` — scope to the application's security group only
- Multi-AZ or provisioned IOPS storage in a course sandbox — cost without benefit for lab traffic
- Leaving `deletion_protection` or `skip_final_snapshot` at their implicit defaults in a disposable environment
- Hardcoding `master_password` in `.tf` files

## See also

- `ai/skills/aws/dynamodb_modeling.md` — the NoSQL alternative and when it fits better
- `ai/skills/aws/iam_policies.md` — least-privilege IAM for RDS management actions (not DB-level auth)
- `ai/skills/terraform/terraform_governance.md` — mandatory tags, budget, and per-service cost awareness
- `ai/skills/terraform/state_management.md` — backend considerations when `master_password` must not appear in state in plaintext logs
