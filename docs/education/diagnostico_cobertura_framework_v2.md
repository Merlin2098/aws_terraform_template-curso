# Diagnóstico de Cobertura del Framework `ai/` frente al Temario del Curso AWS Data Engineering (v2)

> **Naturaleza del documento:** informe de diagnóstico. No propone implementaciones
> ni edita artefactos. Sirve como insumo para una fase posterior de planificación y
> definición de especificaciones.
>
> **Fuentes analizadas:** `docs/education/temario_aws_v2.md` (9 sesiones) y la
> totalidad del directorio `ai/` (configuración, runtime, tooling, políticas,
> dominios y 71 skills).
>
> **Método:** análisis funcional y pedagógico. No se compararon nombres de archivo;
> se evaluó el propósito, las responsabilidades y el comportamiento esperado de cada
> artefacto contra los objetivos de aprendizaje de cada sesión.

---

## 1. Naturaleza del framework `ai/`

Antes de evaluar cobertura conviene entender qué **es** el framework, porque
condiciona toda la lectura pedagógica.

El directorio `ai/` es un **sistema de guía para agentes de IA** (Claude Code),
no un temario ni un conjunto de material didáctico. Su diseño está orientado a
**producir código de calidad en un repositorio host**, no a **enseñar conceptos a
una persona**. Sus componentes son:

| Componente | Rol real | Naturaleza |
|---|---|---|
| `ai/skills/` (71 archivos `.md`) | Recetas de patrones y buenas prácticas que el agente aplica al generar código | Guía prescriptiva, orientada a *hacer*, no a *explicar* |
| `ai/skills.yaml` | Índice canónico de slugs de skills | Configuración |
| `ai/domains/` | Navegación semántica por dominio (AWS, Terraform, Python, data, shell, SaaS, frontend, docs, quality) | Mapa de navegación |
| `ai/policies/global.md` | 10 políticas transversales (spec-before-code, seguridad por defecto, guardrails SPEC-009, IAM cross-module, simplicidad) | Reglas de gobierno |
| `ai/context.yaml` + `ai/runtime/` + `ai/tools/` | Generación de contexto (`inspect_project`, `refresh_context`, grafo de dependencias, registro de skills, treemap) | Automatización de contexto para el agente |
| `ai/installer.py` | Distribución del framework a repos host con detección de divergencias por hash | Infraestructura de plantilla |
| `ai/hooks/treemap.py` | Hook de generación de treemap | Utilidad de contexto |

**Consecuencia central para la evaluación:** el framework cubre bien la
**dimensión de construcción** ("¿cómo escribo bien este recurso de AWS/Terraform?")
pero **no fue diseñado para la dimensión de enseñanza** ("¿cómo explico este
concepto, en qué orden, con qué laboratorio guiado y qué criterio de evaluación?").
Esta distinción atraviesa todos los hallazgos.

### 1.1 Dos niveles de profundidad en los skills

Los skills no son homogéneos. Conviven dos generaciones claramente distinguibles:

- **Skills profundos y accionables** (~production-grade): `lambda_packaging.md`,
  `athena_patterns.md`, `bedrock_client.md`, `bedrock_permissions.md`,
  `terraform_governance.md`, `etl_patterns.md`, `s3_presigned_urls.md`,
  `cognito_auth.md`. Incluyen código real, tablas de decisión, errores comunes con
  causa y solución, y referencias cruzadas. Alto valor.

- **Skills-esbozo (stubs)**: `s3_data_lake.md`, `glue_jobs.md`, `iam_policies.md`,
  `step_functions.md`, `eventbridge.md`, `modules.md`. Son listas de viñetas
  ("When to use / Best practices / Avoid") de 15-40 líneas sin código ni ejemplos.
  Útiles como recordatorio para un agente, insuficientes como material de referencia
  para un alumno que ve el tema por primera vez.

Esta asimetría es la brecha de calidad más importante, porque varios de los
skills-esbozo corresponden a temas **centrales** del temario (S3 Data Lake, Glue,
Step Functions, EventBridge).

---

## 2. Análisis por sesión

Para cada sesión: objetivos → capacidades requeridas → artefactos → contribución →
cobertura → justificación.

### Sesión 1 — Fundamentos de AWS y Preparación del Entorno

- **Objetivos:** Cloud computing, regiones/AZ, modelo de responsabilidad
  compartida, IAM (usuarios/grupos/roles), mínimo privilegio, AWS CLI, entorno de
  desarrollo, Git, introducción a Claude Code, y **control de costos desde el día 1**
  (Calculadora de precios, Cost Explorer, Budgets con alerta).
- **Capacidades requeridas:** material conceptual de fundamentos; guía de bootstrap
  de cuenta/CLI/usuario IAM; configuración de un Budget con alerta; guía de uso de
  Claude Code en el flujo del curso.
- **Artefactos relacionados:**
  - `ai/skills/aws/iam_policies.md` — IAM (roles/mínimo privilegio), pero **stub** y
    orientado a *policies de recursos*, no a *creación de un usuario IAM humano*.
  - `ai/skills/terraform/terraform_governance.md` — **Budget con alerta SNS al 80%/100%**,
    Cost Explorer via tags, awareness de costo por servicio. **Fuerte cobertura del
    control de costos**, aunque desde Terraform (aún no se ha visto Terraform en S1).
  - `ai/skills/shell/cli_automation.md` — patrones seguros de CLI (git, terraform,
    docker, aws) con validate-before-apply. Contribuye al hábito de CLI.
  - `AGENTS.md` — presencia de Claude Code y contrato de trabajo asistido por IA.
- **Cobertura:** **Parcial.**
- **Justificación:** El *control de costos* está sorprendentemente bien cubierto
  (fortaleza). Pero faltan por completo: material de fundamentos conceptuales
  (cloud, regiones/AZ, responsabilidad compartida), guía de **AWS CLI** como tal
  (configuración `aws configure`, perfiles, validación de acceso), y el flujo de
  **creación de un usuario IAM humano + budget desde consola** (el temario en S1 aún
  no usa Terraform, pero el único artefacto de budget del framework es Terraform-only).

### Sesión 2 — Infrastructure as Code con Terraform

- **Objetivos:** IaC, workflow de Terraform, providers/resources/variables/outputs/
  locals/data sources, modules, state, remote backend (S3), organización del proyecto,
  pre-commit para generar contexto del agente.
- **Capacidades requeridas:** guía de estructura de módulos; gestión de state y
  backend remoto; estilo/organización; el mecanismo real de pre-commit → contexto.
- **Artefactos relacionados:**
  - `ai/skills/terraform/modules.md` — estructura de módulo (stub, pero correcto).
  - `ai/skills/terraform/state_management.md` — **backend local vs S3, locking nativo
    con `use_lockfile`, higiene de state**. Buen skill, cubre el objetivo de state/backend.
  - `ai/skills/terraform/terraform_style.md`, `terraform_governance.md`,
    `iam_least_privilege.md`, `environment_promotion.md` — refuerzan organización y
    gobierno.
  - `ai/context.yaml` + `ai/tools/refresh_context.py` + `ai/hooks/treemap.py` —
    **este ES el "pre-commit que genera contexto del agente"** mencionado en el
    temario. Es un diferenciador real y demostrable.
- **Cobertura:** **Completa** (para los objetivos técnicos de Terraform base).
- **Justificación:** Es el dominio **mejor cubierto** del framework (16 skills de
  Terraform). El laboratorio (crear bucket S3 → modularizar → plan/apply) está
  soportado por `modules.md` + `state_management.md` + `s3_data_lake.md`. Además el
  tema "pre-commit para generar contexto del agente" tiene una implementación real y
  única en `ai/runtime`/`ai/tools`, algo que ningún curso estándar puede mostrar.
  Riesgo: hay 16 skills de Terraform, muchos de nivel avanzado (Stacks, orchestration,
  import discovery, CI/CD, refactoring) que **exceden** el alcance de una sesión
  introductoria (ver §5, sobre-dimensionamiento).

### Sesión 3 — Data Lakes con Amazon S3

- **Objetivos:** fundamentos de Data Lake, buckets/objetos/organización de datasets,
  versionado, lifecycle policies, bucket policies, buenas prácticas.
- **Capacidades requeridas:** guía de arquitectura de data lake (capas), versionado,
  lifecycle, policies de bucket, seguridad.
- **Artefactos relacionados:**
  - `ai/skills/aws/s3_data_lake.md` — bronze/silver/gold, Parquet, particionado,
    lifecycle, block public access, KMS. **Cubre los conceptos… pero es un stub de
    30 líneas sin ejemplos de configuración.**
  - `ai/skills/data/etl_patterns.md` — refuerza el modelo de capas.
  - `ai/skills/aws/s3_presigned_urls.md` — profundo, pero orientado a upload de app,
    no a organización de data lake.
  - `terraform_governance.md` — política de versionado **deshabilitado por defecto**
    (útil, pero **choca conceptualmente** con el temario S3 que pide "enseñar
    versionado"; ver Riesgos).
- **Cobertura:** **Parcial.**
- **Justificación:** Los conceptos están nombrados pero no desarrollados con la
  profundidad que un alumno necesita. No hay ejemplo concreto de **lifecycle policy**
  ni de **bucket policy** en HCL/JSON. La guía de seguridad ("KMS", "block public
  access") se menciona sin mostrarse. Contraste llamativo: `athena_patterns.md`
  (sesión 6) es exhaustivo, mientras el fundamento S3 (sesión 3, más temprano y más
  básico) es de los más pobres.

### Sesión 4 — Serverless y Contenedores

- **Objetivos:** serverless, Lambda, API Gateway, IAM roles, ZIP deployments;
  cuándo usar imágenes; Docker/Dockerfile/build; Amazon ECR; Lambda vía container
  image. Foco: **las dos formas de desplegar una Lambda**.
- **Capacidades requeridas:** guía de Lambda; **árbol de decisión ZIP vs imagen**;
  Dockerfile para Lambda; build/push a ECR; Terraform de ambos modos.
- **Artefactos relacionados:**
  - `ai/skills/aws/lambda_functions.md` — **árbol de decisión de packaging (R1–R6),
    regla boto3, binarios nativos.** Excelente, exactamente el foco de la sesión.
  - `ai/skills/aws/lambda_packaging.md` — **Dockerfile de Lambda, `docker_push.sh`,
    regla `--provenance=false`, Terraform ECR + Lambda-image, orden de despliegue,
    tabla de pitfalls.** Uno de los mejores skills del framework.
  - `ai/skills/aws/api_gateway.md` — HTTP vs REST, proxy, CORS, throttling, authorizer.
- **Cobertura:** **Completa.**
- **Justificación:** El objetivo declarado ("conocer las dos formas de desplegar una
  Lambda") está cubierto con material de nivel producción. La única matización
  pedagógica: el skill de packaging **empuja hacia ECR** por razones de ingeniería
  (pyarrow, R3) que pueden ser demasiado avanzadas para introducir el concepto; para
  el aula habría que simplificar el "por qué" antes que el "cómo". Docker en sí
  (fundamentos de imágenes/Dockerfile genérico) sólo aparece **en el contexto de
  Lambda**, no como tema propio — suficiente para el temario, que también lo enmarca
  así.

### Sesión 5 — Bases de Datos

- **Objetivos:** SQL vs NoSQL; cuándo relacional; cuándo DynamoDB; Amazon RDS
  (visión general); Amazon DynamoDB; modelado básico de tablas. Lab: crear tabla
  DynamoDB, insertar/consultar; demo guiada de RDS.
- **Capacidades requeridas:** guía de DynamoDB (modelado, PK/SK, operaciones);
  criterio SQL vs NoSQL; visión general de RDS.
- **Artefactos relacionados:**
  - `ai/skills/saas/database.md` — PostgreSQL/Supabase (Alembic, soft delete). **No
    es AWS RDS ni DynamoDB**; es del stack SaaS, ajeno al curso.
  - `ai/skills/sql/sql_workflow_guidance.md` — organización de SQL, no motores.
- **Cobertura:** **No cubierta.**
- **Justificación:** **Brecha crítica y confirmada por búsqueda exhaustiva:** no
  existe skill de **DynamoDB** ni de **Amazon RDS** en todo `ai/`. No hay material de
  modelado NoSQL, ni criterio SQL-vs-NoSQL, ni patrones de tabla DynamoDB. La única
  guía de base de datos apunta a Supabase/Postgres del dominio SaaS, que no forma
  parte del curso. Esta es la sesión con **peor cobertura del temario**.

### Sesión 6 — Procesamiento de Datos

- **Objetivos:** AWS Glue (Crawlers, Data Catalog, ETL Jobs, Triggers); Amazon
  Athena; **Lake Formation** (gobierno de datos); **Athena vs Redshift** (comparación
  conceptual); flujo general de un pipeline analítico.
- **Capacidades requeridas:** Glue jobs; **Crawlers + Data Catalog**; Athena
  (consultas, particiones, workgroup/costos); comparación Athena/Redshift; intro a
  Lake Formation.
- **Artefactos relacionados:**
  - `ai/skills/aws/glue_jobs.md` — patrón de Glue **job** (stub). Cubre el *job*,
    pero **no Crawlers ni Data Catalog** (solo los nombra el temario, el skill no los
    desarrolla).
  - `ai/skills/data/athena_patterns.md` — **exhaustivo**: ciclo de consulta,
    paginación, partition pruning, partition projection, workgroup con cutoff de
    costo. Excelente cobertura de Athena.
  - `ai/skills/data/etl_patterns.md` — flujo bronze/silver/gold, encaja el "flujo
    general de pipeline analítico".
- **Cobertura:** **Parcial.**
- **Justificación:** **Athena: completa y sobresaliente.** **Glue: parcial** (job sí,
  Crawler/Catalog/Triggers no desarrollados; y el skill es stub). **Lake Formation:
  no cubierta** (cero menciones en `ai/`). **Athena vs Redshift: no cubierta**
  (cero menciones de Redshift). Los dos temas "Nuevo" de esta sesión son brechas
  totales.

### Sesión 7 — Orquestación y Streaming

- **Objetivos:** por qué orquestar; Step Functions y sus estados; EventBridge
  (triggers por eventos); **intro conceptual a streaming — Amazon Kinesis** (qué es,
  batch vs streaming, sin lab).
- **Capacidades requeridas:** Step Functions (estados, retry, catch); EventBridge
  (reglas, scheduling, triggers); material conceptual de Kinesis/streaming.
- **Artefactos relacionados:**
  - `ai/skills/aws/step_functions.md` — **stub** (estados nombrados, sin ASL ni
    ejemplo). Pero `error_handling_pipeline.md` y `etl_patterns.md` describen la
    integración Catch de Step Functions con más detalle que el propio skill.
  - `ai/skills/aws/eventbridge.md` — **stub** (routing, cron, triggers; sin ejemplo).
  - `ai/skills/python/error_handling_pipeline.md` — integración typed-error ↔ Step
    Functions Catch. Aporta profundidad real al "manejo de fallos" de la orquestación.
- **Cobertura:** **Parcial.**
- **Justificación:** Step Functions y EventBridge están **conceptualmente presentes
  pero son stubs**; el material más útil para orquestación vive indirectamente en los
  skills de error handling y ETL. **Kinesis/streaming: no cubierta** (cero menciones).
  El lab (orquestar el pipeline de S6 con Step Functions + trigger EventBridge) es
  factible pero el alumno no encontrará en el framework un ejemplo de definición de
  máquina de estados ni de regla EventBridge.

### Sesión 8 — IA Generativa aplicada a AWS

- **Objetivos:** Amazon Bedrock, foundation models, prompt engineering, integración
  con Lambda, Claude Code sobre AWS, casos de uso. Lab: consumir Bedrock desde Lambda
  usando **datos reales del pipeline S6-S7**.
- **Capacidades requeridas:** cliente Bedrock; permisos/activación de modelos;
  integración Lambda↔Bedrock; versionado de prompts; guardas de costo/contexto.
- **Artefactos relacionados:**
  - `ai/skills/python/bedrock_client.md` — **invoke/converse, retry con backoff,
    parseo defensivo de JSON, guarda de ventana de contexto.** Excelente.
  - `ai/skills/aws/bedrock_permissions.md` — **IAM + activación manual de acceso a
    modelos + ARNs cross-region + smoke test.** Excelente, y advierte del error
    #1 de primer despliegue.
  - `ai/skills/data/etl_patterns.md` — **versionado de prompts, contrato de schema de
    salida, routing por confianza.** Cubre "prompt engineering" aplicado.
  - `ai/skills/aws/lambda_functions.md` / `lambda_packaging.md` — integración con
    Lambda y empaquetado.
- **Cobertura:** **Completa.**
- **Justificación:** Junto con S4 y Terraform, es de las sesiones **mejor cubiertas**.
  El framework aporta material de nivel producción para Bedrock, incluyendo detalles
  operativos (activación de acceso, cross-region, throttling) que rara vez aparecen en
  material educativo. El "prompt engineering" está cubierto de forma aplicada
  (versionado + contrato de salida). Encaja perfecto con el ajuste del temario de
  conectar IA con el pipeline previo.

### Sesión 9 — Proyecto Final (referencia del docente + proyecto del alumno)

- **Objetivos:** proyecto end-to-end (Terraform → S3 → Glue/Athena → Step Functions →
  Bedrock); revisión de arquitectura; buenas prácticas Terraform/AWS; documentación y
  publicación en GitHub; certificación recomendada; checklist de entrega.
- **Capacidades requeridas:** integración de todo el stack; guía de buenas prácticas
  transversales; guía de documentación/README; criterios de revisión/calidad.
- **Artefactos relacionados:**
  - **Toda la cadena de skills** (S3, Glue, Athena, Step Functions, Bedrock,
    Terraform) — el framework provee las piezas del pipeline de referencia.
  - `ai/skills/quality/` (`simplicity.md`, `over_engineering_review.md`,
    `debt_ledger.md`) + `ai/policies/global.md` — criterios de "buenas prácticas"
    accionables.
  - `ai/skills/docs/` (`doc_review.md`, `spec_adr_review.md`, `commit_messages.md`,
    `code_review_comments.md`) — **documentación y publicación en GitHub**, revisión
    de README, mensajes de commit. Muy alineado con el checklist de entrega.
  - `ai/policies/global.md` (SPEC-009, seguridad por defecto, IAM cross-module) —
    define el "nivel de calidad esperado" del proyecto del docente.
- **Cobertura:** **Parcial → Completa** (según se hereden las brechas de S3/Glue/DynamoDB).
- **Justificación:** El framework está **muy bien posicionado como definición de
  "nivel de calidad esperado"** para el proyecto de referencia: políticas de gobierno,
  skills de revisión, guía de documentación y commits. Las brechas se heredan de las
  sesiones fuente (Glue Crawler/Catalog stub, S3 lifecycle/policy sin ejemplo). El
  checklist mínimo del alumno (Terraform + S3 versionado/lifecycle + Glue + Athena +
  orquestación + Bedrock + README) es soportable, con la salvedad de que "versionado
  S3" contradice la política del framework (ver Riesgos).

---

## 3. Matriz de cobertura

| Tema del curso | Objetivos de aprendizaje | Capacidades requeridas | Artefactos relacionados | Cobertura | Observaciones |
|---|---|---|---|---|---|
| **S1 — Fundamentos + Costos** | Cloud, IAM, mínimo privilegio, AWS CLI, Claude Code, Budgets/Cost Explorer | Fundamentos conceptuales; bootstrap CLI/usuario IAM; Budget con alerta | `iam_policies.md` (stub), `terraform_governance.md`, `cli_automation.md`, `AGENTS.md` | **Parcial** | Control de costos bien cubierto (vía Terraform). Faltan fundamentos conceptuales, guía AWS CLI y creación de usuario IAM humano desde consola |
| **S2 — Terraform / IaC** | Workflow, módulos, state, backend S3, pre-commit→contexto | Módulos, state/backend, estilo, mecanismo de contexto | `modules.md`, `state_management.md`, `terraform_style.md`, `environment_promotion.md`, `context.yaml`+`runtime/`+`treemap.py` | **Completa** | Dominio mejor cubierto. "Pre-commit que genera contexto" es un diferenciador real. Riesgo de sobre-dimensionamiento (16 skills, varios avanzados) |
| **S3 — Data Lake S3** | Data lake, versionado, lifecycle, bucket policies | Arquitectura de capas, versionado, lifecycle, policies, seguridad | `s3_data_lake.md` (stub), `etl_patterns.md`, `s3_presigned_urls.md` | **Parcial** | Conceptos nombrados sin ejemplos. Falta lifecycle policy y bucket policy concretas. Versionado choca con política del framework |
| **S4 — Serverless + Contenedores** | Lambda, ZIP vs imagen, Docker, ECR, API Gateway | Árbol ZIP/imagen, Dockerfile Lambda, build/push ECR | `lambda_functions.md`, `lambda_packaging.md`, `api_gateway.md` | **Completa** | Material nivel producción. Ajustar el "por qué ECR" para el aula (razones avanzadas) |
| **S5 — Bases de Datos** | SQL vs NoSQL, DynamoDB, RDS, modelado | DynamoDB (modelado/ops), criterio SQL/NoSQL, visión RDS | (ninguno de AWS) — `saas/database.md` es Supabase/Postgres | **No cubierta** | **Brecha crítica.** No existe skill de DynamoDB ni RDS en todo `ai/` |
| **S6 — Procesamiento** | Glue (Crawler/Catalog/Job/Trigger), Athena, Lake Formation, Athena vs Redshift | Glue completo, Athena, gobierno, comparación analítica | `glue_jobs.md` (stub, solo job), `athena_patterns.md`, `etl_patterns.md` | **Parcial** | Athena sobresaliente. Glue solo cubre "job". Lake Formation y Redshift: brechas totales |
| **S7 — Orquestación + Streaming** | Step Functions, EventBridge, Kinesis (concepto) | Estados/retry/catch, reglas/scheduling, streaming | `step_functions.md` (stub), `eventbridge.md` (stub), `error_handling_pipeline.md` | **Parcial** | SF y EventBridge son stubs; profundidad real está en error-handling. Kinesis: brecha total |
| **S8 — IA Generativa** | Bedrock, FM, prompt engineering, integración Lambda | Cliente Bedrock, permisos/activación, prompts, guardas | `bedrock_client.md`, `bedrock_permissions.md`, `etl_patterns.md`, `lambda_*.md` | **Completa** | Sesión mejor cubierta junto a S4. Detalles operativos poco frecuentes en material educativo |
| **S9 — Proyecto Final** | Integración end-to-end, buenas prácticas, docs, GitHub, certificación | Todo el stack + calidad + documentación + revisión | Cadena completa de skills + `quality/` + `docs/` + `policies/global.md` | **Parcial→Completa** | Fuerte como "definición de nivel de calidad esperado". Hereda brechas de S3/S5/S6 |

**Síntesis de cobertura:**

| Cobertura | Sesiones |
|---|---|
| **Completa** | S2 (Terraform), S4 (Serverless/Contenedores), S8 (IA Generativa) |
| **Parcial** | S1 (Fundamentos), S3 (Data Lake), S6 (Procesamiento), S7 (Orquestación), S9 (Proyecto) |
| **No cubierta** | S5 (Bases de Datos) |

---

## 4. Análisis transversal del framework

### 4.1 Artefactos de alto valor para el curso (preservar)

- **`athena_patterns.md`, `bedrock_client.md`, `bedrock_permissions.md`,
  `lambda_packaging.md`, `lambda_functions.md`, `terraform_governance.md`,
  `etl_patterns.md`, `error_handling_pipeline.md`, `s3_presigned_urls.md`** — material
  de referencia de nivel producción, directamente reutilizable en las sesiones
  correspondientes.
- **`ai/policies/global.md`** — define el "estándar de calidad" del proyecto de
  referencia (S9) de forma explícita y accionable (seguridad por defecto, guardrails
  de costo/observabilidad, mínimo privilegio, IAM cross-module).
- **`ai/skills/quality/`** (simplicity, over-engineering, debt ledger) — enseña
  **criterio de ingeniería**, no un servicio; muy valioso para formar buen juicio en
  el proyecto final.
- **`ai/skills/docs/`** — soporta directamente el objetivo de S9 (README,
  documentación, commits, publicación en GitHub).
- **`ai/context.yaml` + `ai/runtime/` + `ai/tools/` + `treemap.py`** — es la
  materialización del tema "pre-commit para generar contexto del agente" (S2). Único
  y demostrable.

### 4.2 Artefactos reutilizables sin modificación

- Los skills profundos de AWS/Python listados en 4.1.
- Los skills de Terraform base: `state_management.md`, `terraform_style.md`,
  `iam_least_privilege.md`, `environment_promotion.md`.
- Políticas globales y skills de calidad/documentación.

### 4.3 Artefactos que requieren simplificación para contexto educativo

- **Skills-esbozo de temas centrales**: `s3_data_lake.md`, `glue_jobs.md`,
  `step_functions.md`, `eventbridge.md`, `iam_policies.md`, `modules.md`. No es que
  sobren — es que están **por debajo** del nivel didáctico necesario y deberían
  elevarse al estándar de los skills profundos (con ejemplos), no simplificarse.
- **`lambda_packaging.md`**: excelente pero **empuja a ECR** por razones avanzadas; en
  el aula conviene una versión conceptual del árbol de decisión antes del detalle.
- **Los 16 skills de Terraform**: para un curso introductorio, el subconjunto
  relevante es ~5 (modules, state, style, governance, iam_least_privilege). El resto
  (Stacks, orchestration, import discovery, mocks, refactoring, ci_cd, testing,
  observability) es ruido pedagógico en el índice que consulta el alumno/agente.

### 4.4 Artefactos innecesarios para este curso

- **Todo el dominio SaaS** (`ai/skills/saas/*` — 10 skills: FastAPI, Supabase, RBAC,
  Railway/Vercel, VPS/Nginx, DNS/email, analytics de negocio). No aparece en ninguna
  sesión del temario; es de otro tipo de proyecto. Presente sólo por ser una
  plantilla genérica.
- **Todo el dominio Frontend** (`react_vite_aws.md`, `api_client_patterns.md`,
  `file_upload_ux.md`) y **Cognito/CloudFront** — el temario no incluye frontend ni
  autenticación de usuarios finales.
- **`textract.md`, `sqs_patterns.md`** — no aparecen en el temario (SQS se usa
  internamente en algunos skills, pero no es tema del curso). Textract pertenece al
  caso de uso OCR del template, ajeno al temario.
- **Skills de shell PowerShell/Bash avanzados** (`powershell_windows_admin.md`,
  `powershell_json_yaml.md`, etc.) — utilidad marginal para los objetivos del curso.

> Estos artefactos no son "malos": son evidencia de que `ai/` es una **plantilla
> multipropósito** (deriva de un proyecto SaaS/OCR real), no un framework diseñado
> para *este* curso. Para uso educativo, gran parte del catálogo es superficie
> innecesaria que conviene ocultar o podar.

### 4.5 Capacidades importantes que hoy no existen

Brechas de **contenido técnico** (confirmadas por búsqueda exhaustiva en `ai/`):

1. **DynamoDB** — inexistente (bloquea S5).
2. **Amazon RDS** — inexistente (bloquea S5).
3. **Glue Crawlers + Data Catalog** — el skill de Glue solo cubre "job" (parcial S6).
4. **AWS Lake Formation** — inexistente (brecha S6).
5. **Athena vs Redshift** (comparación conceptual) — inexistente (brecha S6).
6. **Amazon Kinesis / streaming** (conceptual) — inexistente (brecha S7).
7. **AWS CLI** como skill (configuración, perfiles, validación) — inexistente (S1).
8. **Bootstrap de cuenta / usuario IAM humano / Budget desde consola** — el único
   budget del framework es Terraform, pero S1 aún no usa Terraform (brecha S1).
9. **Fundamentos conceptuales** (cloud computing, regiones/AZ, modelo de
   responsabilidad compartida) — el framework asume conocimiento previo (brecha S1).

### 4.6 Capacidades que deberían incorporarse para mejorar la experiencia pedagógica

Brechas de **naturaleza** (el framework es "para hacer", no "para enseñar"):

- **Capa didáctica ausente:** los skills no tienen objetivos de aprendizaje,
  progresión, "explicación del porqué" para principiantes, ni preguntas de
  autoevaluación. Son recetas para un agente experto, no lecciones.
- **Sin laboratorios guiados:** no hay guiones paso a paso de los labs, ni datasets
  de ejemplo, ni criterios de "hecho".
- **Sin rúbrica de evaluación:** el checklist de entrega de S9 existe en el temario
  pero no hay artefacto en `ai/` que lo operacionalice como criterio evaluable.
- **Sin secuenciación pedagógica:** `domains/index.md` organiza por dominio técnico,
  no por sesión/progresión del curso. No hay mapa "sesión → skills relevantes".
- **Nivel único (experto):** no hay graduación principiante→avanzado; todo skill
  asume el vocabulario de un ingeniero senior.

---

## 5. Hallazgos

### 5.1 Fortalezas

- **Terraform, Serverless/ECR, Bedrock e IA generativa: cobertura de nivel
  producción** (S2, S4, S8). Material que la mayoría de cursos no ofrece.
- **Control de costos y gobierno** (`terraform_governance.md`, políticas SPEC-009):
  Budgets, tags obligatorios, awareness de costo por servicio, Cost Explorer. Alineado
  con el nuevo énfasis del temario en costos desde el día 1.
- **Athena**: `athena_patterns.md` es ejemplar (particiones, projection, workgroup con
  guardas de costo).
- **Criterio de ingeniería explícito**: skills de calidad + políticas globales
  transmiten *cómo pensar*, no sólo *qué escribir* — alto valor formativo para S9.
- **Diferenciador único**: el sistema de generación de contexto (`ai/runtime` + hooks +
  pre-commit) materializa un tema del temario (S2) que ningún curso genérico puede
  demostrar con código propio.
- **Seguridad y mínimo privilegio "by default"**: coherente con los objetivos de IAM
  de S1.

### 5.2 Brechas

- **Bloqueante — S5 Bases de Datos:** sin DynamoDB ni RDS, la sesión no tiene soporte
  alguno en el framework.
- **S6 incompleta:** Glue Crawler/Data Catalog no desarrollados; Lake Formation y
  Athena-vs-Redshift inexistentes (los dos temas "Nuevo" de la sesión).
- **S7 incompleta:** Step Functions y EventBridge son stubs; Kinesis inexistente.
- **S3 superficial:** conceptos S3 sin ejemplos de lifecycle/bucket policy.
- **S1 parcial:** faltan fundamentos conceptuales, AWS CLI y bootstrap
  cuenta/usuario/budget desde consola.
- **Asimetría de profundidad:** temas básicos y tempranos (S3 Data Lake, Glue) están
  peor documentados que temas avanzados y tardíos (Athena, Bedrock), invirtiendo la
  curva pedagógica esperada.

### 5.3 Riesgos

- **Contradicción de versionado S3:** el temario (S3 y checklist S9) pide **enseñar y
  usar versionado**, mientras `terraform_governance.md` (SPEC-009 §8.3) exige
  versionado **deshabilitado por defecto**. Un alumno siguiendo el framework recibiría
  guía contraria al objetivo de la sesión. Debe reconciliarse explícitamente
  (p.ej. "en el lab se activa deliberadamente y se documenta").
- **Ruido/dispersión:** ~30% del catálogo (SaaS, frontend, Cognito, Textract, shell
  admin) es irrelevante al curso y puede confundir a alumnos y al agente sobre qué es
  material del curso.
- **Nivel demasiado avanzado:** varios skills asumen contexto senior (packaging por
  pyarrow, cross-region inference, partition projection) que puede abrumar en una
  primera exposición si se usan tal cual como material didáctico.
- **Desalineación de propósito:** usar un framework "para agentes" como si fuera
  "material de curso" puede llevar a que se confunda "el agente sabe hacerlo" con "el
  alumno aprendió a hacerlo".

### 5.4 Oportunidades de simplificación

- **Podar/ocultar dominios ajenos** al curso (SaaS, frontend, Cognito, Textract,
  shell admin) para reducir la superficie a lo relevante.
- **Reducir el índice de Terraform** al subconjunto introductorio (~5 skills) para las
  sesiones del curso, dejando los avanzados como material opcional.
- **Un solo mapa "sesión → skills"** reemplazaría la navegación por dominio técnico
  para el contexto educativo.

### 5.5 Oportunidades de mejora

- **Elevar los skills-esbozo** de temas centrales (S3, Glue, Step Functions,
  EventBridge, IAM) al estándar de los skills profundos (ejemplos, código, errores
  comunes).
- **Cubrir las brechas técnicas** (DynamoDB, RDS, Crawler/Catalog, Lake Formation,
  Kinesis, Redshift-comparativa, AWS CLI, bootstrap S1).
- **Añadir una capa didáctica** por encima de los skills: objetivos de aprendizaje,
  laboratorios guiados, datasets de ejemplo, rúbrica de evaluación (checklist S9
  operacionalizado).
- **Reconciliar la política de versionado S3** con el objetivo pedagógico de la sesión.

---

## 6. Resumen ejecutivo

**¿El framework está preparado para soportar el curso?**
**Parcialmente.** Es un excelente **soporte de construcción** para tres sesiones
(Terraform, Serverless/ECR, IA Generativa) y para el criterio de calidad del proyecto
final, pero **no es un framework pedagógico**: fue diseñado para guiar a un agente que
produce código, no para enseñar conceptos a personas. Tiene además brechas técnicas
concretas que impiden cubrir una sesión completa (Bases de Datos) y dejan otras a
medias (Procesamiento, Orquestación, Data Lake).

**¿Qué porcentaje aproximado del temario está cubierto?**
Estimación funcional: **~55–60%** del temario tiene soporte utilizable.
- Completa: 3 de 9 sesiones (**~33%**).
- Parcial: 5 de 9 sesiones (aportan valor, con brechas).
- No cubierta: 1 de 9 sesiones (S5).
Ponderando por profundidad real (stubs vs skills completos), la cobertura *efectiva*
para uso directo en aula se acerca más al **~50%**.

**¿Cuáles son las principales brechas?**
1. **DynamoDB y RDS** (S5) — inexistentes; bloquean la sesión completa.
2. **Glue Crawler/Data Catalog, Lake Formation, Athena vs Redshift** (S6).
3. **Kinesis/streaming, y profundidad de Step Functions/EventBridge** (S7).
4. **Fundamentos conceptuales, AWS CLI y bootstrap de costos desde consola** (S1).
5. **Profundidad insuficiente** de S3 Data Lake (lifecycle/bucket policy sin ejemplos).
6. **Ausencia de capa didáctica** transversal (objetivos, labs guiados, rúbrica).

**¿Qué cambios tendrían mayor impacto para convertirlo en framework pedagógico?**
1. **Añadir una capa de enseñanza** sobre los skills (objetivos de aprendizaje,
   laboratorios paso a paso, datasets de ejemplo, rúbrica de evaluación) — convierte
   "guía para agente" en "material de curso".
2. **Cerrar las brechas técnicas** de S5 (DynamoDB/RDS) y los temas "Nuevo" de S6/S7
   (Lake Formation, Redshift-comparativa, Kinesis).
3. **Elevar los skills-esbozo** de temas centrales al nivel de los skills profundos.
4. **Crear un mapa "sesión → skills"** y **podar el catálogo ajeno** al curso.
5. **Reconciliar la contradicción de versionado S3**.

**¿Qué elementos deberían preservarse por su valor educativo?**
- Los **skills profundos**: `athena_patterns`, `bedrock_client`, `bedrock_permissions`,
  `lambda_packaging`, `lambda_functions`, `etl_patterns`, `error_handling_pipeline`,
  `terraform_governance`.
- Las **políticas globales** (`ai/policies/global.md`) como definición del estándar de
  calidad del proyecto final.
- Los **skills de calidad** (`simplicity`, `over_engineering_review`, `debt_ledger`) y
  de **documentación** (`docs/`) — enseñan criterio y soportan la entrega de S9.
- El **sistema de generación de contexto** (`ai/runtime` + hooks + pre-commit) como
  demostración viva del tema de S2.
- El **enfoque de costo/seguridad "by default"**, alineado con el nuevo énfasis del
  temario.

---

*Fin del informe de diagnóstico. Este documento no modifica artefactos ni propone
implementaciones; su propósito es alimentar una fase posterior de planificación y
definición de especificaciones.*
