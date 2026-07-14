# Kinesis / Streaming Intro Pattern

## When to use

- Explaining when continuous, low-latency ingestion is worth the added operational cost over batch
- Reviewing whether a proposed design actually needs streaming or is over-engineering a batch problem
- Conceptual introduction — this course's labs remain batch-first; no dedicated streaming lab

## Core idea

Streaming is not a strictly better version of batch — it trades simplicity
and cost for lower latency and continuous processing. Most data engineering
workloads (including every lab in this course) are correctly served by batch
processing (Glue jobs on a schedule). Reach for streaming only when the
business requirement is genuinely "seconds, not hours," not by default.

---

## Batch vs streaming

| | Batch | Streaming |
|---|---|---|
| Latency | Minutes to hours | Seconds to sub-second |
| Cost model | Pay for compute during scheduled runs | Pay for continuously provisioned or on-demand shard capacity |
| Operational complexity | Low — a scheduled job that starts and stops | Higher — consumers must handle checkpointing, shard scaling, ordering |
| Failure recovery | Re-run the job | Requires checkpoint/offset management to avoid reprocessing or gaps |
| Fits this course's labs | Yes — Glue jobs on a schedule (Session 6/7) | No dedicated lab — conceptual only |

Default to batch. Introduce streaming only when a concrete requirement (fraud
detection, live dashboards, sub-minute alerting) demands it.

---

## Kinesis Data Streams vs Kinesis Data Firehose

| | Data Streams | Firehose |
|---|---|---|
| When to use | Custom, low-latency consumers with full control over processing | Simple delivery to a destination (S3, Redshift, OpenSearch) with built-in buffering |
| Scaling unit | Shards (manually or auto-scaled) | Fully managed, no shard management |
| Consumers | Custom application code (KCL, Lambda) | None — Firehose delivers directly to the destination |
| Typical course-relevant use | Not used in labs — conceptual only | Would be the natural fit if streaming ingestion to S3 were introduced |

For a course introducing streaming conceptually, Firehose is the easier
mental model: "a managed pipe from a stream into S3," directly connecting to
the bronze layer in `ai/skills/aws/s3_data_lake.md`.

---

## Minimal sketch — Firehose to S3 (conceptual, not a lab exercise)

```hcl
resource "aws_kinesis_firehose_delivery_stream" "events_to_s3" {
  name        = "${local.name_prefix}-events-to-bronze"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose.arn
    bucket_arn = aws_s3_bucket.data_lake.arn
    prefix     = "bronze/streaming_events/"

    buffering_size     = 5   # MB — smaller batches, more frequent S3 writes
    buffering_interval  = 60  # seconds — max delay before flushing to S3
  }

  tags = local.common_tags
}
```

`buffering_size`/`buffering_interval` are the levers that trade near-real-time
delivery against S3 request cost — smaller/shorter buffers mean lower
latency but more, smaller S3 objects (worse for later Athena scan
efficiency).

---

## Cost and when NOT to stream

- A provisioned Kinesis Data Stream bills for shard-hours continuously,
  regardless of traffic — similar to the standing-cost trap described for
  RDS in `ai/skills/aws/rds_overview.md`.
- On-demand mode removes shard planning but still costs more per unit of
  data than an equivalent batch Glue job for the same daily volume.
- If the data only needs to be queryable within hours, batch is cheaper and
  simpler — this describes every lab in this course.

---

## Common errors (conceptual awareness, not hands-on)

| Symptom | Cause | Fix |
|---|---|---|
| Small, numerous S3 objects degrade Athena query performance | Buffering interval/size set too aggressively low | Increase `buffering_interval`/`buffering_size`, or compact objects downstream |
| Shard throughput exceeded | Under-provisioned shard count for write volume, or a hot partition key | Increase shard count or improve partition key cardinality (same principle as DynamoDB hot partitions) |
| Out-of-order processing downstream | Assumed strict ordering across shards, which Kinesis does not guarantee globally | Use a partition key that groups related events on the same shard if order matters within that group |

---

## Avoid

- Introducing streaming because it sounds more advanced, when batch meets the actual latency requirement
- Standing up a Kinesis Data Stream for a course lab with no genuine low-latency requirement
- Assuming global ordering across all shards
- Aggressive Firehose buffering settings that fragment S3 output into many tiny objects

## See also

- `ai/skills/aws/eventbridge.md` — routing/scheduling, which is not a substitute for a stream but is often confused with one
- `ai/skills/aws/sqs_patterns.md` — queuing with guaranteed delivery, the right choice when streaming's throughput isn't needed
- `ai/skills/data/etl_patterns.md` — the batch bronze/silver/gold flow this course uses instead
- `ai/skills/aws/s3_data_lake.md` — the destination bronze layer for either batch or streaming ingestion
