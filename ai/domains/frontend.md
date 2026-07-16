# Domain: Frontend (AWS-integrated)

## Purpose

Guidance for building and deploying React SPAs that integrate with AWS backends
(API Gateway, Lambda, S3, CloudFront, Cognito). This domain covers the build
toolchain, AWS deployment pattern, API client design, and file upload UX.

Next.js projects are detected automatically (via `package.json`'s `next`
dependency — see `ai/tools/inspect_project.py`'s `js_stack` detection) and
fall under this domain too. The existing skill below is written for a
Vite SPA; Next.js differs in env-variable convention (`NEXT_PUBLIC_*` instead
of `VITE_*`/`import.meta.env`) and typically uses SSR/App Router routing
instead of a client-only build — apply the general React/API-client/upload
guidance here, but do not assume the Vite-specific deploy sequence applies
as-is to a Next.js project. A dedicated Next.js skill is not written yet.

---

## Scope

| In scope | Out of scope |
|---|---|
| React + Vite build and environment configuration | AWS infrastructure declaration (see `ai/domains/terraform.md`) |
| Next.js projects (detected via `package.json`, general React guidance applies) | Python Lambda code (see `ai/domains/python.md`) |
| S3 + CloudFront deploy and cache invalidation | |
| Axios client with API Gateway auth headers | |
| File upload via S3 presigned URLs | |
| Loading / error / empty state conventions | |

---

## Skills

| Skill | File | Description |
|---|---|---|
| React + Vite + AWS deploy | `ai/skills/frontend/react_vite_aws.md` | Vite env variables, S3 sync deploy sequence, CloudFront cache invalidation, CSP headers |
| API client patterns | `ai/skills/frontend/api_client_patterns.md` | Centralised axios client, request/response interceptors, retry logic, abort controller, three-state pattern |
| File upload UX | `ai/skills/frontend/file_upload_ux.md` | Presigned URL upload flow, file validation, XHR progress tracking, drag-and-drop, pipeline status polling |

---

## Policies

No domain-specific policies beyond the global set. See [`ai/policies/global.md`](../policies/global.md).

Key global policies with strong frontend implications:

- **Security By Default** — API keys and tokens must never be committed to source; use Vite env variables (`.env.local`, `.env.production`) and exclude them from git. CSP headers must be configured on the CloudFront distribution.
- **Configuration Over Hardcoding** — API base URLs and feature flags must come from `import.meta.env`, never from inline strings.

---

## References

- Global policies: `ai/policies/global.md`
- Domain index: `ai/domains/index.md`
- Related domains: `ai/domains/aws.md` (CloudFront, S3, API Gateway, Cognito)
- Spec that governs domain structure: `specs/rework/SPEC-FW-003.md`
