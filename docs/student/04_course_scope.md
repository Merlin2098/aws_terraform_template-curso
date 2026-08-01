# Mapa de Scope del Curso — Sesión → Skills (`ai/skills/`)

> Documento de navegación, no ejecutable. Reduce la superficie cognitiva del
> framework `ai/` para el curso AWS Data Engineering (temario v2) sin borrar
> ni marcar skills como obsoletos — el resto del catálogo (frontend, Cognito,
> CloudFront, Textract, shell avanzado, Terraform excedente) permanece
> disponible para otros proyectos host que reutilicen esta plantilla.
>
> Complementa, no reemplaza, `ai/domains/index.md` (navegación general por
> dominio técnico). Este archivo navega por **sesión del curso**.

Referencia: `docs/student/03_temario.md` (temario) y
`docs/internal/legacy/diagnostico_cobertura_framework_v2.md` (diagnóstico de
cobertura que motivó el cierre de brechas registrado aquí).

---

## Lista maestra in-scope (por dominio)

| Dominio | Skills in-scope del curso |
|---|---|
| `aws` | `aws_cli`, `account_bootstrap_console`, `iam_policies`, `s3_data_lake`, `dynamodb_modeling`, `rds_overview`, `lambda_functions`, `lambda_packaging`, `glue_jobs`, `glue_crawler_catalog`, `lake_formation_intro`, `step_functions`, `eventbridge`, `kinesis_streaming_intro`, `bedrock_permissions` |
| `data` | `athena_patterns`, `athena_vs_redshift`, `etl_patterns`, `data_contracts`, `data_quality_guidance` |
| `python` | `bedrock_client`, `error_handling_pipeline`, `python_project_guidance` |
| `terraform` | `state_management`, `terraform_governance`, `terraform_observability` |
| `quality` / `docs` | `simplicity`, `over_engineering_review`, `doc_review`, `commit_messages` (soporte transversal para S9) |

Todo lo que no aparece en esta lista (dominio `frontend`, `cognito_auth`,
`cloudfront_s3_hosting`, `textract`, skills avanzados de `shell`, y el resto
de `terraform` — stacks, orchestration, import, mocks, ci_cd, refactoring,
testing, observability, security) sigue existiendo en `ai/skills/` pero está
**fuera del alcance de este curso**. No se borra: sirve a otros proyectos
host de esta plantilla.

---

## Sesión → Skills

### Sesión 1 — Fundamentos de AWS y Preparación del Entorno

| Skill | Aporte a la sesión |
|---|---|
| `ai/skills/aws/account_bootstrap_console.md` | Bootstrap día-1 en consola: usuario IAM, MFA, Budget con alerta antes de que exista Terraform |
| `ai/skills/aws/aws_cli.md` | Instalación, `aws configure`, perfiles, precedencia de credenciales, validación de acceso |
| `ai/skills/aws/iam_policies.md` | Usuario humano vs role, principio de mínimo privilegio |
| `docs/student/02_mcp_setup.md` | Instalación de los MCP de AWS Documentation y Terraform en Claude Code |

### Sesión 2 — Infrastructure as Code con Terraform

| Skill | Aporte a la sesión |
|---|---|
| `docs/student/01_setup_windows.md` | Instalación de Terraform y AWS CLI en Windows |
| `docs/student/05_terraform_cheatsheet.md` | Flujo de comandos día a día (`init`/`fmt`/`validate`/`plan`/`apply`) |
| `ai/skills/terraform/state_management.md` | Backend local vs S3, locking nativo, higiene de state |
| `ai/context.yaml` + `ai/tools/refresh_context.py` + `ai/hooks/treemap.py` | Implementación real de "pre-commit para generar contexto del agente" |

> Diseño de módulos y convenciones de estilo genéricas de Terraform (antes
> cubiertos por los skills locales `modules.md`, `environment_promotion.md`,
> `terraform_style.md`, hoy eliminados por redundantes con el MCP oficial) se
> consultan mediante el MCP de Terraform. El principio de mínimo privilegio
> de IAM vive en `ai/skills/aws/iam_policies.md`. Ver
> `docs/student/02_mcp_setup.md` para la instalación del MCP.

### Sesión 3 — Data Lakes con Amazon S3

| Skill | Aporte a la sesión |
|---|---|
| `ai/skills/aws/s3_data_lake.md` | Capas bronze/silver/gold, lifecycle, bucket policy, versionado (con nota de excepción educativa) |
| `ai/skills/terraform/terraform_governance.md` | Reconciliación de la política de versionado con el objetivo pedagógico de la sesión |

### Sesión 4 — Serverless y Contenedores

| Skill | Aporte a la sesión |
|---|---|
| `ai/skills/aws/lambda_functions.md` | Árbol de decisión ZIP vs imagen |
| `ai/skills/aws/lambda_packaging.md` | Dockerfile, build/push a ECR, Terraform Lambda-image |
| `ai/skills/aws/api_gateway.md` | Complementario, si la sesión cubre API Gateway |

### Sesión 5 — Bases de Datos

| Skill | Aporte a la sesión |
|---|---|
| `ai/skills/aws/dynamodb_modeling.md` | PK/SK, single-table básico, boto3 CRUD, `aws_dynamodb_table` |
| `ai/skills/aws/rds_overview.md` | Cuándo relacional, engine/instancia, `aws_db_instance` destruible |

### Sesión 6 — Procesamiento de Datos

| Skill | Aporte a la sesión |
|---|---|
| `ai/skills/aws/glue_jobs.md` | Job de transformación (bronze → silver/gold) |
| `ai/skills/aws/glue_crawler_catalog.md` | Crawler + Data Catalog + triggers |
| `ai/skills/data/athena_patterns.md` | Ciclo de consulta, particiones, workgroup con guardas de costo |
| `ai/skills/aws/lake_formation_intro.md` | Gobierno del data lake sobre el Catalog |
| `ai/skills/data/athena_vs_redshift.md` | Comparación conceptual (sin laboratorio) |

### Sesión 7 — Orquestación y Streaming

| Skill | Aporte a la sesión |
|---|---|
| `ai/skills/aws/step_functions.md` | Máquina de estados ASL, Retry/Catch, Map |
| `ai/skills/aws/eventbridge.md` | Reglas de schedule y event-pattern, triggers |
| `ai/skills/aws/kinesis_streaming_intro.md` | Introducción conceptual a streaming (sin laboratorio) |
| `ai/skills/python/error_handling_pipeline.md` | Errores tipados que Step Functions captura |

### Sesión 8 — IA Generativa aplicada a AWS

| Skill | Aporte a la sesión |
|---|---|
| `ai/skills/python/bedrock_client.md` | `invoke_model`/`converse`, retry, parseo defensivo, guarda de contexto |
| `ai/skills/aws/bedrock_permissions.md` | IAM + activación de acceso a modelos + ARNs cross-region |
| `ai/skills/data/etl_patterns.md` | Versionado de prompts y contrato de salida (prompt engineering aplicado) |

### Sesión 9 — Proyecto Final

| Skill | Aporte a la sesión |
|---|---|
| Toda la cadena de skills de S2–S8 | Piezas del pipeline de referencia end-to-end |
| `ai/skills/quality/simplicity.md`, `over_engineering_review.md` | Criterio de "buenas prácticas" para revisar el proyecto |
| `ai/skills/docs/doc_review.md`, `commit_messages.md` | Documentación y publicación en GitHub |
| `ai/policies/global.md` | Nivel de calidad esperado (seguridad por defecto, SPEC-009, mínimo privilegio) |

---

## Mantenimiento de este mapa

Al añadir o elevar un skill relevante para el curso: añadirlo a la lista
maestra y a la fila de sesión correspondiente. Este archivo es un mapa
estático de solo lectura — no lo consume ningún script ni loader; existe
para que quien prepare o dicte una sesión sepa qué skills consultar sin
recorrer los 8 dominios completos del framework.
