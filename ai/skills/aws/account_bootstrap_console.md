# Account Bootstrap (Console) Pattern

## When to use

- Day one of the course, before Terraform or the CLI is configured
- Setting up a new AWS account for a student or a sandbox environment
- Establishing cost control before any billable resource exists

## Core idea

Two things must happen in the AWS console before any other work begins:
never operate as the root user for daily tasks, and never let spend
accumulate without an alert. Both are one-time, click-path setup steps that
Terraform cannot automate on a brand-new account — there is no IAM identity
yet for Terraform to authenticate as, and Billing preferences are an
account-level console setting.

---

## Step 1 — Secure the root user

The root user is created with the account and has unrestricted access,
including the ability to close the account and change billing. Use it only
for the steps below, then stop using it.

1. Sign in as root once.
2. Enable MFA on the root user (**IAM** → **Root user** → **Add MFA**, or
   **Security credentials** from the account menu).
3. Do not create an access key for root. If one exists from account
   creation, delete it.

---

## Step 2 — Create the first IAM identity

Root must never be used for day-to-day work, including running the AWS CLI
or Terraform. Create a human IAM user (or, in an organization with IAM
Identity Center, a federated user) before doing anything else:

1. **IAM** → **Users** → **Create user** → name it (e.g. `student-01`).
2. Enable console access if the student will use the AWS console directly.
3. Enable MFA on this user as well.
4. Attach a least-privilege policy — see `ai/skills/aws/iam_policies.md` for
   the policy document itself. For a course sandbox, an account-scoped
   managed policy limited to the services used in the syllabus is
   preferable to `AdministratorAccess`.
5. Create an access key for CLI use (**Security credentials** tab →
   **Create access key** → *Command Line Interface (CLI)* use case).

Hand the access key to `ai/skills/aws/aws_cli.md` (`aws configure`) — do not
paste it into chat, code, or any file that gets committed.

---

## Step 3 — Create a Budget with an alert

Do this before creating any billable resource, not after the first lab.

1. **Billing and Cost Management** → **Budgets** → **Create budget**.
2. Choose **Cost budget**, monthly period.
3. Set a limit appropriate for a course sandbox (e.g. $25–$50/month).
4. Add an alert threshold at **80% of actual spend** and a second one at
   **100% of forecasted spend** — the same two-notification pattern the
   Terraform-managed budget uses later (see
   `ai/skills/terraform/terraform_governance.md`).
5. Enter an email address that will actually be checked during the course.

This is the console equivalent of the `aws_budgets_budget` resource
Terraform will manage from Session 2 onward. Once infrastructure-as-code is
introduced, the budget can be re-created under Terraform management — do not
leave two duplicate budgets active long-term.

---

## Step 4 — Confirm the working region

Pick one region for the entire course (this template defaults to
`us-east-1`) and select it consistently in the console top-right region
selector. Resources created in the wrong region are a common source of
"it's not there" confusion in later sessions.

---

## Step 5 — Enable billing alerts (account-level, one-time)

**Billing preferences** → enable **Receive Billing Alerts**. This is required
for CloudWatch billing metric alarms to function, and is independent of the
Budget created in Step 3.

---

## Handoff to CLI and Terraform

Once Steps 1–5 are complete, the student has: a non-root IAM identity with
an access key, a budget with alerts active, and a confirmed region. From
here:

- `ai/skills/aws/aws_cli.md` — configure the CLI with the access key
- `ai/skills/aws/iam_policies.md` — the policy document attached in Step 2
- `ai/skills/terraform/terraform_governance.md` — the Terraform-managed
  budget and tagging that supersede the console budget from Session 2 onward

---

## Common errors

| Symptom | Cause | Fix |
|---|---|---|
| Budget alert email never arrives | Wrong email, or email not confirmed (AWS sends a subscription confirmation) | Check spam folder for the SNS subscription confirmation and confirm it |
| Student can't see resources they created | Console region differs from the region used in Step 2's access key session | Reselect the confirmed region in the console top-right selector |
| `aws sts get-caller-identity` returns the wrong account | Access key was created under the wrong IAM user, or root's own key was used | Re-create the key under the intended IAM user; never use a root access key |

---

## Avoid

- Using the root user for anything beyond Steps 1–3
- Creating a root access key
- Skipping the Budget step until after the first lab — cost surprises are the
  most common early-course incident
- Granting `AdministratorAccess` to the student's IAM user by default when a
  narrower policy covers the syllabus services

## See also

- `ai/skills/aws/aws_cli.md` — CLI configuration using the access key created here
- `ai/skills/aws/iam_policies.md` — least-privilege policy document for the IAM user
- `ai/skills/terraform/terraform_governance.md` — Terraform-managed budget that supersedes this console budget
