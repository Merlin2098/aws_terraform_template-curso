# EventBridge Pattern

## When to use

- Triggering a pipeline on a schedule (cron-like) instead of manual execution
- Reacting to an AWS service event (S3 upload, Glue job state change) without polling
- Decoupling producers and consumers across services

## Core idea

EventBridge routes events via rules matched against either a fixed schedule
or an event pattern — never both in the same rule. Choosing the wrong
trigger type (EventBridge vs SQS vs a direct Lambda trigger) for the
workload's actual delivery/ordering needs is the most common design mistake;
EventBridge is for routing and scheduling, not for queuing or guaranteed
ordered delivery.

---

## Schedule-based rule

```hcl
resource "aws_cloudwatch_event_rule" "nightly_pipeline" {
  name                = "${local.name_prefix}-nightly-pipeline"
  description         = "Trigger the pipeline every night at 02:00 UTC"
  schedule_expression = "cron(0 2 * * ? *)"
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "nightly_pipeline" {
  rule      = aws_cloudwatch_event_rule.nightly_pipeline.name
  target_id = "step-functions-pipeline"
  arn       = aws_sfn_state_machine.pipeline.arn
  role_arn  = aws_iam_role.eventbridge_invoke_sfn.arn
}
```

---

## Event-pattern rule — react to an AWS service event

```hcl
resource "aws_cloudwatch_event_rule" "glue_job_state_change" {
  name        = "${local.name_prefix}-glue-job-state-change"
  description = "React to Glue job SUCCEEDED or FAILED state changes"

  event_pattern = jsonencode({
    source      = ["aws.glue"]
    detail-type = ["Glue Job State Change"]
    detail = {
      jobName = [aws_glue_job.bronze_to_silver.name]
      state   = ["SUCCEEDED", "FAILED"]
    }
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "notify_on_job_state" {
  rule      = aws_cloudwatch_event_rule.glue_job_state_change.name
  target_id = "notify-lambda"
  arn       = aws_lambda_function.notify.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notify.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.glue_job_state_change.arn
}
```

`aws_lambda_permission` is required whenever the target is a Lambda function
— without it, EventBridge matches the rule but the invocation silently fails
with no error visible in the rule itself; the failure only appears in the
Lambda's own metrics (or its absence).

---

## Choosing a trigger: pattern vs schedule vs SQS

| Need | Use |
|---|---|
| Run on a fixed cadence (nightly, hourly) | EventBridge scheduled rule (`schedule_expression`) |
| React to an AWS service event (S3 PUT, Glue state change) | EventBridge event-pattern rule |
| Guarantee at-least-once delivery with retry and a dead-letter queue | SQS (see `ai/skills/aws/sqs_patterns.md`) — EventBridge alone has weaker delivery guarantees for high-volume, must-not-lose workloads |
| High-throughput ordered event ingestion | Kinesis (see `ai/skills/aws/kinesis_streaming_intro.md`) — EventBridge is not a stream |

For this course's labs: use a scheduled rule to trigger the Session 6/7
pipeline, and an event-pattern rule as the alternative trigger mentioned in
the syllabus (S3 upload → pipeline start).

---

## S3 upload as a trigger (event pattern)

```hcl
resource "aws_cloudwatch_event_rule" "s3_object_created" {
  name = "${local.name_prefix}-s3-object-created"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = [aws_s3_bucket.data_lake.id] }
      object = { key = [{ prefix = "bronze/" }] }
    }
  })

  tags = local.common_tags
}
```

Requires S3 EventBridge notifications enabled on the bucket
(`aws_s3_bucket_notification` with `eventbridge = true`), a separate,
one-time bucket-level setting.

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| Rule matches (visible in CloudWatch metrics) but the Lambda never runs | Missing `aws_lambda_permission` for `events.amazonaws.com` | Add the permission scoped to the specific rule ARN |
| Scheduled rule never fires | `schedule_expression` uses local time assumptions | `cron()` and `rate()` expressions are always UTC |
| Event pattern never matches | Pattern shape doesn't match the actual event envelope (nested `detail` structure) | Test against a sample event from the AWS service's documented event schema |
| S3 event pattern rule never triggers | EventBridge notifications not enabled on the bucket | Set `eventbridge = true` in `aws_s3_bucket_notification` |

---

## Avoid

- Using EventBridge as a message queue for workloads that need guaranteed, ordered, retryable delivery — use SQS instead
- Mixing `schedule_expression` and `event_pattern` in the same rule (mutually exclusive)
- Forgetting `aws_lambda_permission` when the target is Lambda
- Assuming `cron()` expressions run in local time — they are UTC

## See also

- `ai/skills/aws/sqs_patterns.md` — when guaranteed delivery and DLQ semantics are required instead
- `ai/skills/aws/step_functions.md` — the typical target of a scheduled or event-pattern rule
- `ai/skills/aws/lambda_functions.md` — Lambda-as-target configuration
- `ai/skills/aws/kinesis_streaming_intro.md` — when event volume/ordering needs a stream instead of routing
