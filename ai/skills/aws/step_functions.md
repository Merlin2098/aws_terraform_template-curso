# Step Functions Pattern

## When to use

- Orchestrating a multi-step pipeline (e.g. Glue job → Athena query → Bedrock call)
- Adding explicit retry/catch behavior around AWS SDK integrations
- Replacing manual, sequential script execution with an observable, resumable workflow

## Core idea

Step Functions defines workflows as state machines, not code. Its value is
observability and explicit failure handling — every state's input/output and
every retry/catch decision is visible in the console execution history.
Keep business logic out of the state machine definition itself; states should
call existing Lambda functions, Glue jobs, or other AWS APIs, not embed
transformation logic in ASL.

---

## Minimal state machine — sequential pipeline

```hcl
resource "aws_sfn_state_machine" "pipeline" {
  name     = "${local.name_prefix}-pipeline"
  role_arn = aws_iam_role.step_functions.arn

  definition = jsonencode({
    Comment = "Bronze -> Silver -> Athena query pipeline"
    StartAt = "RunGlueJob"
    States = {
      RunGlueJob = {
        Type     = "Task"
        Resource = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = {
          JobName = aws_glue_job.bronze_to_silver.name
        }
        Retry = [
          {
            ErrorEquals     = ["States.TaskFailed"]
            IntervalSeconds = 30
            MaxAttempts     = 2
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath  = "$.error"
            Next        = "NotifyFailure"
          }
        ]
        Next = "QueryAthena"
      }

      QueryAthena = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.athena_query.arn
        }
        Next = "Success"
      }

      NotifyFailure = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn = aws_sns_topic.pipeline_alerts.arn
          Message  = "Pipeline failed. See execution history for details."
        }
        End = true
      }

      Success = {
        Type = "Succeed"
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_functions.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "step_functions" {
  name              = "/aws/states/${local.name_prefix}-pipeline"
  retention_in_days = 14  # explicit — never omit (SPEC-009)
  tags              = local.common_tags
}
```

The `.sync` suffix on `glue:startJobRun.sync` makes Step Functions wait for
the Glue job to complete before advancing — without it, the state succeeds
immediately after *starting* the job, not after it finishes.

---

## Retry and Catch — the core error-handling primitives

- **`Retry`** — re-attempts the *same* state on a matching error, with
  exponential backoff (`BackoffRate`). Use for transient failures
  (throttling, brief service unavailability).
- **`Catch`** — routes to a *different* state on a matching error, after
  retries are exhausted (or immediately, if no `Retry` is defined). Use for
  permanent failures that need a distinct recovery path (human review queue,
  alert, dead-letter routing).

Match `ErrorEquals` to the typed exceptions raised by pipeline code — see
`ai/skills/python/error_handling_pipeline.md` for how a Lambda's typed
exceptions surface as named errors Step Functions can `Catch` on
individually, rather than lumping every failure into `States.ALL`.

---

## Parallel and Map states

```json
{
  "ProcessAllDocuments": {
    "Type": "Map",
    "ItemsPath": "$.documents",
    "MaxConcurrency": 5,
    "Iterator": {
      "StartAt": "NormaliseDocument",
      "States": {
        "NormaliseDocument": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "Parameters": { "FunctionName": "normalise-document" },
          "End": true
        }
      }
    },
    "Next": "Aggregate"
  }
}
```

Set `MaxConcurrency` explicitly — an unbounded `Map` state can overwhelm a
downstream Lambda's concurrency limit or a shared resource like an RDS
connection pool.

---

## IAM role for the state machine

```hcl
data "aws_iam_policy_document" "step_functions_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "step_functions" {
  name               = "${local.name_prefix}-step-functions"
  assume_role_policy = data.aws_iam_policy_document.step_functions_trust.json
  tags               = local.common_tags
}
```

Attach scoped permissions per integrated service (`glue:StartJobRun`,
`glue:GetJobRun`, `lambda:InvokeFunction`, `sns:Publish`) — see
`ai/skills/aws/iam_policies.md` for the policy-document pattern.

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| State "succeeds" but the Glue job is still running | Used `glue:startJobRun` instead of the `.sync` variant | Append `.sync` to wait for task completion |
| Every failure looks identical in the execution history | Business logic raises generic `Exception` instead of typed errors | Raise typed errors (see `error_handling_pipeline.md`) and `Catch` on specific `ErrorEquals` |
| `Map` state overwhelms a downstream service | No `MaxConcurrency` set | Set an explicit concurrency ceiling |
| No logs for a failed execution | Missing `logging_configuration` or log group | Declare `aws_cloudwatch_log_group` with `retention_in_days` and wire `logging_configuration` |

---

## Avoid

- Embedding transformation or business logic directly in ASL — states should call existing Lambda/Glue/API resources
- Using `Catch: States.ALL` as the only error handling when typed errors are available upstream
- Unbounded `Map` state concurrency
- Omitting `.sync` on long-running service integrations (Glue, ECS) when the next state depends on completion
- Relying on the default Step Functions log group instead of declaring one explicitly

## See also

- `ai/skills/python/error_handling_pipeline.md` — typed exceptions this state machine catches by name
- `ai/skills/aws/eventbridge.md` — triggering this state machine on a schedule or event
- `ai/skills/aws/glue_jobs.md` — the `.sync` integration pattern for Glue jobs
- `ai/skills/terraform/terraform_observability.md` — mandatory log group and retention conventions
