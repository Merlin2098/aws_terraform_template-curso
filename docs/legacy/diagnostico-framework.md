# Informe de diagnóstico — Framework de plantilla AWS + Terraform

> **Alcance:** análisis de todo el repositorio **excepto** `src/`, `tests/` y
> artefactos generados (`.ai/`, `artifacts/*.zip`, `.venv/`, `uv.lock`).
> **Naturaleza:** informe de diagnóstico. **No** contiene propuestas de cambio.
> **Fecha:** 2026-07-13.

---

## 0. Qué es este repositorio (visión de una frase)

Es una **plantilla instalable** (no una aplicación). Se copia dentro de otro
repositorio ("host") mediante un instalador, y aporta convenciones de Python +
SQL + Terraform + testing + guía para agentes de IA, seleccionadas por
**capacidades** (capabilities) activables. No hay ejecución de IA en tiempo de
ejecución: la capa `ai/` es guía y generación de contexto, no orquestación.

El repositorio tiene, por tanto, **dos vidas simultáneas** que conviene separar
mentalmente antes de leer el resto del informe:

1. **La plantilla como producto** (el motor que se instala en otros repos):
   `ai/installer.py`, `ai/runtime/`, `install_*.py`, la máquina de estado de
   versiones/hashes.
2. **El proyecto de ejemplo que la plantilla instala** (lo que un estudiante
   realmente tocaría): `infra/`, `Makefile`, `scripts/`, `docs/`, contenido de
   `ai/skills/`.

Buena parte de la complejidad "innecesaria para estudiantes" proviene de mezclar
estas dos vidas en un mismo checkout.

---

## 1. Qué componentes existen

Agrupados por rol funcional.

### A. Motor de instalación / versionado (la plantilla-como-producto)
| Componente | Archivos |
|---|---|
| Instaladores (entrypoints CLI) | [install_windows.py](../../install_windows.py), [install_linux.py](../../install_linux.py) |
| Lógica de instalación/actualización | [ai/installer.py](../../ai/installer.py) (~1200 líneas) |
| Estado de instalación (host) | `.framework-version.json` (generado en el host; manifest sha256 + tree_digest) |

### B. Runtime de capacidades y contexto (`ai/runtime/`)
| Componente | Archivo | Rol |
|---|---|---|
| Registro de capacidades | [capability_registry.py](../../ai/runtime/capability_registry.py) | Carga descriptores YAML de `ai/capabilities/` |
| Perfil (schema del `.template-profile.yaml`) | [profile.py](../../ai/runtime/profile.py) | Parsea/renderiza el perfil activo |
| Resolución de perfil | [project_profile.py](../../ai/runtime/project_profile.py) | Resuelve dependencias transitivas, extras, groups, scanners, hooks |
| Config de contexto | [config.py](../../ai/runtime/config.py) | Lee `ai/context.yaml` |
| Bundle de contexto | [context_bundle.py](../../ai/runtime/context_bundle.py) | Genera `.ai/context_bundle.yaml` |
| Registro de skills | [skill_registry.py](../../ai/runtime/skill_registry.py) | Filtra skills activas por capacidad |
| Grafo de dependencias | [dependency_graph.py](../../ai/runtime/dependency_graph.py) | Escáner AST Python **y** regex JS/TS |

### C. Herramientas de inspección / refresco (`ai/tools/`, `ai/hooks/`)
| Componente | Archivo |
|---|---|
| Inspección del proyecto | [ai/tools/inspect_project.py](../../ai/tools/inspect_project.py) |
| Refresco de artefactos de contexto | [ai/tools/refresh_context.py](../../ai/tools/refresh_context.py) |
| Generación de treemap | [ai/hooks/treemap.py](../../ai/hooks/treemap.py) |

### D. Descriptores de capacidades (`ai/capabilities/`)
8 descriptores YAML en 7 categorías: `business/saas`, `cloud/aws`,
`databases/supabase`, `frameworks/react`, `infrastructure/terraform`,
`languages/python`, `platform/domains`, `platform/vps`. Cada uno declara
`depends_on`, `paths`, `dependencies` (extras/groups), `scanners`, `artifacts`.

### E. Guía para IA (`ai/skills/`, `ai/domains/`, `ai/policies/`, `ai/skills.yaml`, `ai/context.yaml`)
~70 archivos de skills en dominios (aws, terraform, python, data, frontend,
saas, shell, docs, quality, sql), un índice de dominios, políticas globales y
dos índices YAML (`skills.yaml`, `context.yaml`).

### F. Scripts de proyecto (`scripts/`)
| Grupo | Archivos |
|---|---|
| Entorno uv | [run_uv_sync.py](../../scripts/run_uv_sync.py) (254 líneas), `linux/*.sh`, `windows/*.ps1` |
| Empaquetado | [package.py](../../scripts/package.py) |
| Restauración | [restore_project.py](../../scripts/restore_project.py) |
| Treemap | [generate_treemap.py](../../scripts/generate_treemap.py) |
| Hooks pre-commit | [hooks/ai_refresh.py](../../scripts/hooks/ai_refresh.py), [hooks/sync_dependencies.py](../../scripts/hooks/sync_dependencies.py) |
| Testing | [testing/run_pytest.py](../../scripts/testing/run_pytest.py), `run_ruff_check.py`, `run_ruff_format.py`, `run_cloud_tests.py`, `check_ssl_regression.py` |

### G. Infraestructura de ejemplo (`infra/`)
Terraform de ejemplo: bucket S3 de artefactos, rol IAM de ejecución (Glue),
CloudWatch log group, SNS + AWS Budgets, backend S3 opcional con native locking.

### H. Orquestación y configuración
[Makefile](../../Makefile), [.pre-commit-config.yaml](../../.pre-commit-config.yaml),
[.claude/settings.json](../../.claude/settings.json), [pyproject.toml](../../pyproject.toml),
[.template-profile.yaml](../../.template-profile.yaml).

### I. Contratos y documentación de diseño
`AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/` (setup Windows/Linux, principios
Terraform, workaround SSL), `specs/` (contratos + rework ADRs/SPECs internos).

---

## 2. Qué problema resuelve cada uno

| Componente | Problema que resuelve |
|---|---|
| **Instaladores + `installer.py`** | Copiar la plantilla a otro repo sin sobrescribir lo que el host posee, y poder **actualizar** sin destruir cambios locales (detección de drift por hash de 3 vías). |
| **Runtime de capacidades** | Que un host active solo lo que necesita (p. ej. solo Python, o AWS+Terraform) y que dependencias/skills/artefactos deriven **automáticamente** de esa elección, con resolución transitiva. |
| **`profile.py` + `.template-profile.yaml`** | Persistir de forma declarativa qué capacidades están activas y la política de dependencias. |
| **`dependency_graph.py` / `inspect_project.py` / `treemap.py`** | Generar contexto legible por IA (grafo de imports, resumen del proyecto, árbol de archivos) **sin** que sea requerido en runtime. |
| **`context_bundle.py` / `skill_registry.py` / `refresh_context.py`** | Producir los artefactos `.ai/*` que resumen el proyecto y las skills activas. |
| **`ai/skills/` + `ai/domains/` + `ai/policies/`** | Biblioteca de patrones y reglas para que el agente de IA trabaje según convenciones del equipo. |
| **`run_uv_sync.py` + hook `sync_dependencies.py`** | Sincronizar el `.venv` con extras/groups según capacidades; evitar re-sync innecesario (hash de archivos de dependencias); mitigar problemas de OneDrive/symlinks en Windows. |
| **`package.py`** | Construir el ZIP de despliegue (código `src/` + `requirements.txt` resuelto, prod-only) para Glue/Lambda. |
| **`restore_project.py`** | Dejar el repo consistente tras clonar/cambiar de rama (sync + refresh + validar que las skills declaradas existen). |
| **Scripts `testing/`** | Envolver `pytest`/`ruff` de forma reproducible y multiplataforma. |
| **`check_ssl_regression.py`** | Detectar la regresión SSL de boto3 en Python 3.14 (workaround documentado). |
| **`infra/`** | Ejemplo mínimo, destruible y de bajo coste de infraestructura AWS. |
| **`Makefile` / wrappers PowerShell** | Comandos explícitos y uniformes; soporte para entornos Windows corporativos sin `make` en PATH. |
| **`AGENTS.md` / `CLAUDE.md`** | Contrato de trabajo para agentes de IA (fuentes de conocimiento, límites de aprobación). |
| **`specs/`** | Contratos duraderos del proyecto y ADRs internos del rediseño del framework (`rework/`). |

---

## 3. Qué dependencias existen entre ellos

Grafo lógico (flechas = "depende de / consume"):

```text
install_windows.py ─┐
install_linux.py  ──┴─► ai/installer.py
                            │
                            ├─► ai/runtime/capability_registry.py  (lee ai/capabilities/*.yaml)
                            └─► ai/runtime/profile.py              (renderiza .template-profile.yaml)

.template-profile.yaml ─► profile.py ─► project_profile.py
                                             │  (resuelve capacidades + transitivas)
                                             ├─► capability_registry.py
                                             ├─► extras/groups ──► run_uv_sync.py, package.py
                                             ├─► scanners ───────► dependency_graph.py
                                             └─► artifacts/paths ─► refresh_context.py, skill_registry.py

ai/context.yaml ─► config.py ─► inspect_project.py, treemap.py, context_bundle.py

refresh_context.py ─┬─► inspect_project.py
                    ├─► context_bundle.py ─► skill_registry.py ─► project_profile.py
                    ├─► dependency_graph.py
                    └─► treemap.py
                       └► genera .ai/* (opcional, no requerido en runtime)

Makefile ─► scripts/* (package, run_uv_sync, testing/*, hooks/ai_refresh, restore, treemap)
.pre-commit-config.yaml ─► hooks/ai_refresh.py, hooks/sync_dependencies.py
restore_project.py ─► run_uv_sync.py + refresh_context.py + skill_registry.py
```

Observaciones sobre el acoplamiento:

- **`project_profile.py` es el cuello de botella central**: casi todo (deps,
  scanners, skills, artefactos) pasa por su resolución. Es el módulo con mayor
  "radio de impacto".
- **`config.py` (lee `ai/context.yaml`)** es una segunda raíz de configuración,
  separada de la de capacidades. Existen **dos sistemas de configuración
  paralelos** (`.template-profile.yaml` vía `profile.py`, y `ai/context.yaml`
  vía `config.py`) que se cruzan en `refresh_context.py`.
- La capa `.ai/` generada es **hoja del grafo**: nada en runtime la consume
  (confirmado por `README` y `ai/context.yaml: rules`).
- `installer.py` está **desacoplado** de la capa de contexto: instala archivos y
  mantiene el manifest de hashes; no invoca `refresh_context`.

---

## 4. Cuáles son imprescindibles

Para el **flujo principal de un proyecto instalado** (editar código, sincronizar
entorno, testear, empaquetar, desplegar infra):

| Imprescindible | Motivo |
|---|---|
| `pyproject.toml` + `uv.lock` | Definición de dependencias; sin ellos no hay entorno. |
| `.template-profile.yaml` | Punto de entrada de la selección de capacidades. |
| `ai/runtime/profile.py` + `project_profile.py` + `capability_registry.py` | Resuelven qué extras/groups instalar; los consumen `run_uv_sync.py` y `package.py`. |
| `ai/capabilities/*.yaml` | Datos que alimentan la resolución anterior. |
| `scripts/run_uv_sync.py` (+ wrappers OS) | Crea/sincroniza el `.venv`. |
| `Makefile` | Superficie de comandos explícita del proyecto. |
| `scripts/package.py` | Construye el bundle desplegable. |
| `scripts/testing/run_pytest.py`, `run_ruff_*.py` | Validación básica. |
| `infra/` (si el proyecto usa AWS) | Infraestructura desplegable. |
| `AGENTS.md` / `CLAUDE.md` | Contrato de agente (si se trabaja con IA). |

Para el **flujo de la plantilla-como-producto** (instalar/actualizar en hosts),
además son imprescindibles: `install_*.py` y `ai/installer.py`.

---

## 5. Cuáles podrían eliminarse sin afectar el flujo principal

> "Flujo principal" = editar código → sync entorno → test → empaquetar →
> desplegar infra. Estos componentes **no participan** en esa cadena.

| Candidato a prescindible | Por qué no afecta el flujo principal |
|---|---|
| **Toda la generación `.ai/`**: `refresh_context.py`, `context_bundle.py`, `skill_registry.py`, `dependency_graph.py`, `inspect_project.py`, `treemap.py`, `generate_treemap.py` | El propio repo declara que `.ai/` es opcional y **nunca requerido en runtime**. El código compila, testea y despliega sin regenerar contexto. |
| **Escáner JavaScript/TS de `dependency_graph.py`** | El perfil por defecto solo activa el scanner `python`; el bloque JS/TS (~110 líneas de regex) no se ejercita en un proyecto Python. |
| **`restore_project.py`** | Conveniencia post-clone; sus tres pasos (sync, refresh, validar skills) se pueden hacer manualmente. |
| **Hook `ai_refresh` (pre-commit)** | Solo regenera artefactos opcionales en cada commit. |
| **`check_ssl_regression.py`** | Guardia específica de un bug de Python 3.14; irrelevante fuera de ese entorno. |
| **Máquina de actualización de `installer.py`** (`update_template`, `_classify`, `_detect_local_modifications`, merges append-only, tree_digest) | El **primer install** funciona sin ella; toda la lógica de drift/hash/orphans solo importa al **actualizar** un host ya instalado. |
| **`specs/rework/` (ADR-FW / SPEC-FW)** | Documentación del rediseño interno del framework; no afecta el uso. |
| **`ai/capabilities` no usadas + skills de dominios no activos** (saas, react, supabase, vps, gran parte de terraform/aws) | En un perfil solo-Python, no se cargan. |

> Nota: "eliminable sin afectar el flujo principal" **no** significa "sin valor".
> Varios de estos elementos son el propósito diferenciador del framework
> (guía IA, actualización sin drift). El punto es que el flujo de trabajo
> básico no depende de ellos.

---

## 6. Qué partes agregan complejidad innecesaria para estudiantes

Ordenado por coste cognitivo (mayor primero):

1. **La máquina de estado de instalación/actualización (`ai/installer.py`, ~1200 líneas).**
   Introduce conceptos avanzados —hash de 3 vías (host/state/template),
   `tree_digest`, clases de propiedad (`managed`/`generated`/`append-only`),
   merges TOML/YAML sección a sección, limpieza de huérfanos— que son de nivel
   "diseño de gestor de paquetes", no de aprendizaje de AWS/Terraform. Un
   estudiante no necesita entender esto para usar la plantilla.

2. **Dos sistemas de configuración paralelos.**
   `.template-profile.yaml` (capacidades, vía `profile.py`) **y** `ai/context.yaml`
   (estructura/reglas/artefactos, vía `config.py`) coexisten y se cruzan en
   `refresh_context.py`. Entender "quién configura qué" exige leer ambos árboles.

3. **Resolución transitiva de capacidades con validación de tipos y detección de ciclos.**
   `project_profile.py` valida que el `type` del descriptor coincida con la
   categoría, resuelve `depends_on` recursivamente y detecta ciclos. Es correcto,
   pero es maquinaria pesada para lo que en la práctica son ~8 capacidades.

4. **La capa completa de generación de contexto IA (`.ai/`).**
   Cinco artefactos, un escáner AST + un escáner regex JS, filtrado de skills por
   paths activos. Un estudiante tiende a asumir que "esto se ejecuta y es
   necesario", cuando es opcional y desconectado del runtime.

5. **Multiplataforma triplicada.**
   Para cada operación de entorno hay ruta Windows (PowerShell + `run_make.ps1`
   para entornos corporativos), ruta Linux (`.sh`) y ruta `make`, más el
   detector `uv_command_prefix` (`uv` / `py -3 -m uv` / `python -m uv`). Necesario
   para robustez, pero multiplica los caminos que un principiante debe descartar.

6. **~70 archivos de skills y 10 dominios de IA.**
   La mayoría irrelevantes para un perfil solo-Python. El volumen sugiere que
   "hay que leerlo todo" cuando el sistema lo filtra automáticamente.

7. **`specs/` mezcla dos audiencias.**
   Contratos del proyecto (`specs/README.md`, `specs/project/`) conviven con
   ADRs/SPECs del **rediseño interno del framework** (`specs/rework/`,
   `SPEC-017/018`). Un estudiante no distingue "contrato que debo respetar" de
   "historia de diseño del motor".

### Inconsistencia detectada (no es una propuesta, es un hallazgo)

El `README.md` y `specs/README.md` describen ampliamente una carpeta
**`specs/template/`** (contratos heredados de solo lectura, con archivos
`000-template-spec-format.md` … `003-ai-guidance-layers.md`). **Esa carpeta no
existe** en el árbol actual: solo hay `specs/project/`, `specs/rework/` y los
`SPEC-017/018` de nivel superior. La documentación referencia una estructura que
el repositorio no materializa. Para una variante educativa, esta divergencia
doc-vs-realidad es una fuente de confusión relevante.

---

## Resumen ejecutivo

- El repositorio son **dos cosas en una**: un **motor de plantilla instalable**
  (complejo, nivel "gestor de paquetes") y un **proyecto de ejemplo AWS/data**
  (relativamente sencillo). La complejidad percibida por un estudiante viene casi
  toda del primero.
- El **flujo principal** (perfil → sync entorno → test → package → infra) depende
  de un núcleo pequeño: `pyproject.toml`, `.template-profile.yaml`, `ai/runtime`
  de perfil/capacidades, `run_uv_sync.py`, `package.py`, `testing/`, `Makefile`,
  `infra/`.
- La **capa de contexto IA `.ai/`** y la **máquina de actualización del
  instalador** son las dos áreas más grandes que **no** intervienen en ese flujo
  y concentran la mayor complejidad cognitiva.
- Hay una **divergencia documentación-realidad** en `specs/template/` que
  conviene tener presente.

*Fin del diagnóstico. Sin propuestas de cambio, según lo solicitado.*
