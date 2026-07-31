# Domain: Shell / Scripting

## Purpose

Guidance for generating, validating, and maintaining shell scripts, with
**Git Bash as the default shell** for maximum cross-environment compatibility
(Windows, Linux, WSL, macOS all run the same Bash syntax). PowerShell is
scoped to the one area where it has no Bash equivalent: native Windows
administration (services, registry, scheduled tasks).

This domain covers environment detection, idiomatic Bash scripting, Windows
administration (PowerShell), CLI orchestration, security, testing, and
documentation.

It is the authoritative source for *how to write and validate scripts* — not
for what AWS services do (see `ai/domains/aws.md`) or how Terraform modules are
structured (see `ai/domains/terraform.md`).

---

## Why Git Bash by default

`AGENTS.md` declares Git Bash as the default terminal for this project. The
same rationale applies here: a Bash script written once runs unchanged on
Windows (via Git Bash), Linux, WSL, and macOS. A PowerShell script only runs
natively on Windows (or requires PowerShell Core installed elsewhere) and
introduces a second syntax to maintain. Default to Bash for every script
unless the task is Windows-native administration that Bash cannot reach
(Windows Services, Registry, Scheduled Tasks — see
`ai/skills/shell/powershell_windows_admin.md`).

---

## Scope

| In scope | Out of scope |
|---|---|
| Bash script structure and idioms (primary) | AWS service behaviour and configuration (→ `ai/domains/aws.md`) |
| PowerShell — Windows-only administration (services, registry, scheduled tasks) | Terraform module design (→ `ai/domains/terraform.md`) |
| Environment detection (OS, shell, WSL, Git Bash) | Python automation (→ `ai/domains/python.md`) |
| CLI orchestration (git, terraform, docker, aws, az) — scripting patterns | CI/CD pipeline configuration syntax (→ Terraform MCP/docs) |
| Script security: destructive-op guards, dry-run, secret hygiene | Internal framework or runtime implementation |
| Script testing (ShellCheck, PSScriptAnalyzer, Pester) and documentation | Operational AWS smoke testing templates (→ `ai/skills/aws/aws_smoke_testing.md`) |

---

## Skills

| Skill | File | Description |
|---|---|---|
| Environment detection | `ai/skills/shell/environment_detection.md` | Detect OS, shell type, WSL, and Git Bash before generating scripts; confirms whether Bash is available before falling back |
| Bash core | `ai/skills/shell/bash_core.md` | **Default for all new scripts.** Portable Bash — `set -euo pipefail`, error handling, arg parsing |
| CLI automation | `ai/skills/shell/cli_automation.md` | Safe scripting for git, terraform, docker, aws, az — Bash-first, with a PowerShell variant only where the user's environment requires it |
| PowerShell Windows admin | `ai/skills/shell/powershell_windows_admin.md` | The one legitimate reason to reach for PowerShell: services, registry (with backup), and scheduled tasks — no Bash equivalent exists |
| PowerShell core | `ai/skills/shell/powershell_core.md` | Idiomatic PowerShell fundamentals — use only when `powershell_windows_admin.md` or an explicit user requirement calls for a `.ps1` script |
| PowerShell filesystem | `ai/skills/shell/powershell_filesystem.md` | Safe file/directory operations with mandatory `-WhatIf` — use only when the script must be PowerShell-native; otherwise prefer Bash |
| PowerShell JSON/YAML | `ai/skills/shell/powershell_json_yaml.md` | JSON/YAML parsing in PowerShell — use only inside a PowerShell-native script; otherwise prefer `jq`/`yq` via Bash |
| Script security | `ai/skills/shell/script_security.md` | Destructive-op guards, dry-run, confirmation prompts, secret hygiene — applies to both shells |
| Script quality | `ai/skills/shell/script_quality.md` | ShellCheck, PSScriptAnalyzer, Pester, documentation, and refactoring patterns |

---

## Skill dependency order

```
environment_detection
    └── bash_core                          (default path)
            └── cli_automation
    └── powershell_windows_admin            (Windows-only administration — no Bash equivalent)
            ├── powershell_core
            ├── powershell_filesystem
            └── powershell_json_yaml

script_security      (applies to all scripts regardless of shell)
script_quality       (applies to all scripts regardless of shell)
```

Always apply `environment_detection` first. Default to the `bash_core` →
`cli_automation` path. Only branch into the PowerShell tree when the task is
Windows Services/Registry/Scheduled Tasks administration, or the user
explicitly requires a `.ps1` script for their environment. Layer
`script_security` and `script_quality` on every generated script regardless
of shell.

---

## Policies

This domain is subject to the global policies in [`ai/policies/global.md`](../policies/global.md).

Key constraints:

- **Default to Git Bash** — generate Bash scripts unless the task requires
  native Windows administration or the user explicitly asks for PowerShell.
- **Policy 008 (Simplicity)** — apply the simplicity ladder before introducing
  abstractions; three similar lines is better than a premature helper function.
- **AGENTS.md — Approval Boundaries** — `terraform apply`, `terraform destroy`,
  and overwriting user-owned data always require explicit approval. Scripts that
  invoke these must implement a confirmation gate (see `ai/skills/shell/script_security.md`).
- **AC-3 / AC-4 (SPEC-018)** — all destructive operations require confirmation;
  PowerShell scripts support `-WhatIf` where applicable.

Scripts in this domain may *invoke* AWS and Terraform CLI. The resulting
infrastructure changes remain subject to the approval rules in AGENTS.md and
SPEC-009 (`ai/policies/global.md` §Policy 009).
