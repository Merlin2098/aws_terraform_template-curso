# Domain: Terraform

## Purpose

Guidance for declaring and maintaining this project's AWS infrastructure as code
using Terraform — the project-specific conventions and decisions (module design,
state layout, tagging/budget governance, environment promotion) that a generic
Terraform reference cannot know. It is the authoritative source for how
infrastructure is written and managed in this repo — not what AWS services do
(see `ai/domains/aws.md`), and not generic Terraform mechanics already covered by
the Terraform MCP or official documentation (style/formatting, CI/CD pipeline
shapes, mocks, stacks, resource import, security fundamentals).

---

## Scope

| In scope | Out of scope |
|---|---|
| Terraform module design for this project | AWS service behaviour and usage patterns (see `ai/domains/aws.md`) |
| State backends and remote state layout used here | Python or shell scripts that invoke Terraform |
| Tagging, budget, and cost governance | Application code deployed onto the infrastructure |
| Environment promotion (dev → staging → prod) | Data pipeline logic (see `ai/domains/data-product.md`) |
| Observability outputs (log groups, retention) | Generic Terraform style, CI/CD, testing/mocks, import, or security theory — use the Terraform MCP/docs |

---

## Skills

| Skill | File | Description |
|---|---|---|
| State management | `ai/skills/terraform/state_management.md` | State backends, overrides, and hygiene |
| Observability | `ai/skills/terraform/terraform_observability.md` | CloudWatch log groups, retention policies, mandatory outputs |
| Governance | `ai/skills/terraform/terraform_governance.md` | Tagging enforcement, budget governance, cost awareness, drift management |

For generic Terraform mechanics not tied to this project's own conventions
(module design, directory-per-environment layout, style/formatting, CI/CD
pipeline shapes, mocks, stacks, resource import, security fundamentals,
IAM least-privilege theory) — consult the Terraform MCP or official
HashiCorp documentation directly rather than a local skill; this domain
only keeps skills encoding project-specific decisions. `infra/` is
currently a single flat root module (no `envs/` or `modules/` layer) —
if that changes, module/promotion patterns belong back here as
project-specific skills, not before.

Never hardcode a specific Terraform or provider version constraint in a
skill's prose (e.g. "AWS provider >= 5.81"). Versions drift; query the
Terraform MCP (`get_latest_provider_version`, `search_providers`) for the
current number instead of trusting what's written here.

---

## Policies

No domain-specific policies beyond the global set. See [`ai/policies/global.md`](../policies/global.md).

Key constraints from `AGENTS.md` that are enforced at the Terraform level:

- `terraform apply` and `terraform destroy` require explicit user approval — never run autonomously.
- IAM changes require explicit review before applying.
- S3 versioning must not be enabled by default — only when explicitly requested and justified.
- Every resource must carry `local.common_tags` including `CostCenter`.
- Every deployable module or root module must expose `log_group_name` and
  `log_group_arn` for its log group(s), plus a purpose-named ARN output for
  each principal resource other stacks may need to reference (e.g.
  `artifact_bucket_arn`, `data_job_execution_role_arn`) — not a single
  generic `resource_arn`, since a module producing more than one resource
  (the common case here) has no single ARN that name could mean.
- `terraform.tfstate` must never be deleted or overwritten.

Preferred execution:

- Use `make <target>` when available.
- Run Terraform commands directly from `infra/` — never introduce hidden automation.

---

## References

- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Related domains: `ai/domains/aws.md`
- Agent operational policies: `AGENTS.md` (Approval Boundaries and SPEC-009 sections)
- Spec that governs domain structure: `specs/rework/SPEC-FW-003.md`
