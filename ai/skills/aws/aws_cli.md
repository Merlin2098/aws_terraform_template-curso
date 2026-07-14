# AWS CLI Pattern

## When to use

- Day-one setup, before any Terraform exists
- Validating account access from the terminal
- Diagnosing "works in console, fails from CLI" issues
- Switching between multiple AWS accounts or roles locally

## Core idea

The AWS CLI resolves credentials through a fixed precedence order. Most
first-day failures (`AccessDenied`, wrong account, wrong region) come from a
credential source higher in that order silently overriding the one the user
thinks is active — not from a broken IAM policy.

---

## Installation and first-time configuration

```bash
aws --version
aws configure
```

`aws configure` prompts for and writes to `~/.aws/credentials` and `~/.aws/config`:

```
AWS Access Key ID [None]: AKIA...
AWS Secret Access Key [None]: ...
Default region name [None]: us-east-1
Default output format [None]: json
```

Never commit `~/.aws/credentials` or paste its contents anywhere — see
Policy 007 (Never Send Sensitive Files to External Services) in
`ai/policies/global.md`.

---

## Named profiles

Use named profiles instead of overwriting the default credentials for every
account or role:

```bash
aws configure --profile course-dev
```

```ini
# ~/.aws/config
[profile course-dev]
region = us-east-1
output = json

# ~/.aws/credentials
[course-dev]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
```

Select a profile per command or for the whole shell session:

```bash
aws s3 ls --profile course-dev
export AWS_PROFILE=course-dev   # Linux/macOS/WSL
$env:AWS_PROFILE = "course-dev" # PowerShell
```

---

## Credential precedence (highest wins)

| Order | Source | Typical cause of confusion |
|---|---|---|
| 1 | Command-line options (`--profile`, `--region`) | Explicit flag overrides everything below |
| 2 | Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_PROFILE`, `AWS_REGION`) | A stale `AWS_PROFILE` exported in an old shell session silently wins |
| 3 | CLI credentials/config file (`~/.aws/credentials`, `~/.aws/config`) | The `[default]` profile is used when no `AWS_PROFILE` is set |
| 4 | Container/ECS credentials | Only relevant when running inside a container with an injected role |
| 5 | Instance metadata / EC2 instance role | Only relevant when running on an EC2 instance |

When a command behaves unexpectedly, check environment variables **first**
(`echo $AWS_PROFILE` / `$env:AWS_PROFILE`) — they silently override the file-based
profile the user edited.

---

## Validating access

Always confirm identity before running anything else:

```bash
aws sts get-caller-identity --profile course-dev
```

```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/student-01"
}
```

If this fails, nothing downstream (Terraform, boto3, other CLI commands) will
work — fix credentials before proceeding.

---

## Common commands used in this course

```bash
# Confirm region and identity
aws sts get-caller-identity
aws configure get region

# List resources created in the labs
aws s3 ls
aws dynamodb list-tables
aws lambda list-functions
aws glue get-databases

# Read-only checks before terraform apply
aws iam list-attached-user-policies --user-name student-01
```

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `Unable to locate credentials` | No profile configured, or `AWS_PROFILE` points to a non-existent profile | Run `aws configure --profile <name>` or unset `AWS_PROFILE` |
| Commands hit the wrong account | A stale `AWS_PROFILE` environment variable overrides the intended profile | `echo $AWS_PROFILE` and unset it, or pass `--profile` explicitly |
| `AccessDenied` despite correct-looking policy | Wrong region — the resource exists in a different region than the CLI default | Pass `--region` explicitly or check `aws configure get region` |
| Region mismatch between console and CLI | Console session region differs from `~/.aws/config` default | Match `--region` to the console's selected region |

---

## Avoid

- Hardcoding access keys in scripts or code — use profiles or environment variables
- Leaving `AWS_PROFILE` exported in a shared or long-lived shell session
- Assuming `aws configure` output format affects Terraform or boto3 (it does not — those are separate)
- Skipping `aws sts get-caller-identity` before debugging a deeper failure

## See also

- `ai/skills/aws/account_bootstrap_console.md` — creating the IAM user this profile authenticates as
- `ai/skills/aws/iam_policies.md` — least-privilege policy attached to that user
- `ai/skills/shell/cli_automation.md` — safe scripting patterns for CLI-driven workflows
