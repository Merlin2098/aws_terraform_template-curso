# Domain: Rust

## Purpose

Guidance for writing maintainable Rust code: Cargo project layout, module
boundaries, and testing conventions. This domain focuses on code quality and
structure — not on the AWS services a Rust service might call (see
`ai/domains/aws.md`) or infrastructure that deploys it (see
`ai/domains/terraform.md`).

---

## Scope

| In scope | Out of scope |
|---|---|
| Cargo project structure (`src/main.rs`, `src/lib.rs`, `src/bin/`) | Terraform or infrastructure code |
| Module boundaries and `Cargo.toml` conventions | AWS service configuration (see `ai/domains/aws.md`) |
| Testing patterns (`cargo test`) and `clippy` usage | Frontend JavaScript / TypeScript (see `ai/domains/frontend.md`) |
| Error handling with `Result`/`Option` | |

---

## Skills

| Skill | File | Description |
|---|---|---|
| Project guidance | `ai/skills/rust/rust_project_guidance.md` | Idiomatic Cargo layout, module conventions, `Result`-based error handling, testing and `clippy` |

---

## Policies

No domain-specific policies beyond the global set. See [`ai/policies/global.md`](../policies/global.md).

Key global policies with strong Rust implications:

- **Configuration Over Hardcoding** — read configuration from environment
  variables or a config struct, never from inline literals.
- **Security By Default** — AWS credentials must never appear in code; use
  IAM roles or environment-provided credentials.

---

## References

- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Related domains: `ai/domains/aws.md`, `ai/domains/terraform.md`
