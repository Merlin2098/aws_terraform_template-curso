# Domain: Go

## Purpose

Guidance for writing maintainable Go code: project layout, package
boundaries, and testing conventions. This domain focuses on code quality and
structure — not on the AWS services a Go service might call (see
`ai/domains/aws.md`) or infrastructure that deploys it (see
`ai/domains/terraform.md`).

---

## Scope

| In scope | Out of scope |
|---|---|
| Go project structure (`cmd/`, `internal/`, `pkg/`) | Terraform or infrastructure code |
| Package/module boundaries and `go.mod` conventions | AWS service configuration (see `ai/domains/aws.md`) |
| Testing patterns (`go test`, table-driven tests) | Frontend JavaScript / TypeScript (see `ai/domains/frontend.md`) |
| Error handling with explicit `error` values | |

---

## Skills

| Skill | File | Description |
|---|---|---|
| Project guidance | `ai/skills/go/go_project_guidance.md` | Idiomatic Go layout, module/package conventions, testing and error-handling basics |

---

## Policies

No domain-specific policies beyond the global set. See [`ai/policies/global.md`](../policies/global.md).

Key global policies with strong Go implications:

- **Configuration Over Hardcoding** — read configuration from flags,
  environment variables, or a config struct, never from inline literals.
- **Security By Default** — AWS credentials must never appear in code; use
  IAM roles or environment-provided credentials.

---

## References

- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Related domains: `ai/domains/aws.md`, `ai/domains/terraform.md`
