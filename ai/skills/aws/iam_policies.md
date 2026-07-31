# IAM Policy Pattern

## When to use

- Defining permissions for a human IAM user (console/CLI access)
- Defining an execution role for a service (Lambda, Glue, Step Functions)
- Reviewing any Terraform change that touches IAM
- Diagnosing an `AccessDenied` or `PassRole` error

## Core idea

IAM has two distinct identity shapes with different lifecycles and trust
models: a **user** (a person, with long-lived credentials) and a **role** (an
assumable identity, with short-lived credentials, used by services or
federated humans). Conflating them — attaching broad permissions to a user
"to make it work," or giving a service role wildcard resources — is the most
common security regression in a fast-moving course project. Grant the
minimum actions on the minimum resource ARNs, scoped per service.

---

## Human user vs service role

| | IAM User | IAM Role |
|---|---|---|
| Who/what assumes it | A person, directly | A service (Lambda, Glue) or a person via `sts:AssumeRole` |
| Credentials | Long-lived access key + secret | Short-lived, auto-rotated by STS |
| Created in | `ai/skills/aws/account_bootstrap_console.md` (Step 2) | Alongside the resource that needs it (see Policy 010, IAM cross-module rule) |
| Typical policy | Console/CLI access to the services used in the course | `assume_role_policy` (trust policy) + one or more permission policies |

A course student's IAM user should never be the identity a Lambda function
runs as — that always requires a separate execution role.

---

## Trust policy vs permission policy

A role has two distinct policy documents: the **trust policy** (who can
assume it) and one or more **permission policies** (what it can do once
assumed). Confusing the two is a common source of `AccessDenied` errors that
look like a permissions problem but are actually a trust problem.

```hcl
# Trust policy: only Lambda's service principal may assume this role
data "aws_iam_policy_document" "lambda_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_execution" {
  name               = "${local.name_prefix}-lambda-execution"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
  tags               = local.common_tags
}
```

---

## Permission policy — scoped to actions and ARNs

Never use `Resource: "*"` or an action wildcard (`s3:*`) for anything beyond
a one-off diagnostic. Scope every statement to the specific actions the code
calls and the specific resource ARNs it needs.

```hcl
data "aws_iam_policy_document" "lambda_s3_access" {
  statement {
    sid    = "ReadWriteBronzeBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.bronze.arn}/*",
    ]
  }

  statement {
    sid       = "ListBronzeBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.bronze.arn]  # bucket-level action needs the bucket ARN, not object ARN
  }
}

resource "aws_iam_policy" "lambda_s3_access" {
  name   = "${local.name_prefix}-lambda-s3-access"
  policy = data.aws_iam_policy_document.lambda_s3_access.json
  tags   = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_s3_access.arn
}
```

Note the ARN distinction: bucket-level actions (`s3:ListBucket`) take the
bucket ARN; object-level actions (`s3:GetObject`, `s3:PutObject`) take the
bucket ARN with `/*` appended. Mixing these up is a frequent cause of
`AccessDenied` on an otherwise-correct-looking policy.

---

## Human user policy — console/CLI scoped access

For the IAM user created in `account_bootstrap_console.md`, prefer a
managed or customer policy scoped to the services the course actually uses,
rather than `AdministratorAccess`:

```hcl
data "aws_iam_policy_document" "student_sandbox" {
  statement {
    sid    = "CourseServices"
    effect = "Allow"
    actions = [
      "s3:*",
      "dynamodb:*",
      "lambda:*",
      "glue:*",
      "athena:*",
      "states:*",
      "events:*",
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "cloudwatch:*",
      "logs:*",
      "iam:PassRole",
    ]
    resources = ["*"]  # acceptable only for a personal sandbox account with a budget guardrail
  }
}
```

A resource wildcard here is a deliberate, documented exception for a
single-student sandbox account — not a pattern to carry into any shared or
production account. Pair it with the Budget from
`ai/skills/aws/account_bootstrap_console.md` as the actual guardrail.

---

## `iam:PassRole` — the cross-cutting gotcha

Any principal that creates a resource which itself assumes a role (e.g.
creating a Lambda function with an execution role) needs `iam:PassRole` on
that specific role ARN — a permission entirely separate from being able to
create the Lambda itself.

```hcl
statement {
  sid       = "PassLambdaExecutionRole"
  effect    = "Allow"
  actions   = ["iam:PassRole"]
  resources = [aws_iam_role.lambda_execution.arn]
}
```

Missing this produces an `AccessDenied: ... is not authorized to perform:
iam:PassRole` error at resource-creation time, even when every other
permission is correct.

---

## Permission boundaries (advanced, optional)

A permission boundary caps the maximum permissions an identity can ever have,
even if a later policy attachment grants more. Useful when a course allows
students to create their own IAM roles but must guarantee they can never
escalate beyond a fixed ceiling. Out of scope for a first pass at this
course — introduce only if students provision their own IAM resources.

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `AccessDenied` despite a policy that "looks right" | Action requires the bucket-level ARN but the policy only grants the object-level ARN (or vice versa) | Check the AWS action's required resource type in its documentation; add the missing ARN form |
| `AccessDenied: ... iam:PassRole` when creating a Lambda/Glue job | The creating principal lacks `iam:PassRole` on the specific execution role ARN | Add a scoped `iam:PassRole` statement for that role ARN |
| Role assumption fails with `AccessDenied` for the *assuming* principal | Trust policy's `principals` block doesn't include the actual service or account | Correct the `principals.identifiers` in the trust policy |
| Policy attached but permissions "don't take effect" | Policy attached to the wrong identity (user instead of role, or vice versa) | Verify which identity the code actually runs as before attaching |

---

## Avoid

- `Resource: "*"` or action wildcards (`s3:*`, `iam:*`) outside a documented sandbox exception
- Attaching permissions directly to a user when the workload actually runs as a service role
- Sharing one IAM role across unrelated services "to save time" — separate roles per service (Policy 010)
- Granting `iam:PassRole` with `Resource: "*"` — always scope to the specific role ARN
- Using `AdministratorAccess` as the default policy for a student sandbox user

## See also

- `ai/skills/aws/account_bootstrap_console.md` — creating the human IAM user this policy attaches to
- `ai/skills/aws/aws_cli.md` — validating which identity a profile authenticates as
- `ai/policies/global.md` Policy 010 — IAM cross-module placement rule
