# Informe de migración — de `make` + `uv` + `pyproject.toml` a `pip` + `requirements.txt`

> **Branch:** `curso`.
> **Objetivo declarado:** convertir el repositorio en un framework orientado a
> enseñanza usando **únicamente `pip` + `requirements.txt`**, eliminando
> `Makefile`, `uv`, `pyproject.toml` y `uv.lock`.
> **Naturaleza:** informe de análisis. **No** se implementan cambios.
> **Fecha:** 2026-07-13.

---

## Contexto: dónde vive el acoplamiento

Antes del detalle, el mapa de dependencias entre las herramientas a eliminar:

```text
pyproject.toml ──► define: extras (local/cloud/saas/supabase) + dependency-groups (dev-*)
    ▲                       + [tool.pytest] + [tool.ruff] + versión del framework
    │
    ├── uv.lock            (lockfile que uv resuelve desde pyproject)
    │
    ├── ai/runtime/project_profile.py  ──► LEE pyproject con tomllib para validar
    │       │                                 extras/groups declarados por capacidades
    │       └─ uv_sync_args() / uv_export_args()  ──► construyen comandos `uv`
    │
    ├── ai/capabilities/*.yaml  ──► declaran extras/groups que DEBEN existir en pyproject
    │
    ├── scripts/run_uv_sync.py, scripts/package.py, scripts/hooks/sync_dependencies.py
    │       └─ invocan `uv` y leen pyproject/uv.lock
    │
    ├── scripts/{linux,windows}/setup_env.*, update_venv.*  ──► exigen pyproject + uv
    │
    ├── Makefile  ──► superficie de comandos: todo pasa por run_uv_sync/package/testing
    │       └─ scripts/windows/run_make.ps1  (wrapper para make en Windows)
    │
    └── ai/installer.py  ──► trata pyproject como "append-only", lo mergea sección
            └─ _merge_pyproject() usa tomllib     a sección al instalar en hosts
```

El punto crítico: **el sistema de capacidades está construido sobre el modelo de
`extras` + `dependency-groups` de `pyproject.toml`**, que `pip` +
`requirements.txt` no tienen de forma nativa. Esto no es un cambio de comando; es
un cambio del modelo de dependencias.

---

## 1. Dependencias rotas

Archivos/funciones que **dejarán de funcionar** al retirar las herramientas.

### 1.1 Código Python del runtime

| Archivo | Qué se rompe |
|---|---|
| [ai/runtime/project_profile.py](../../ai/runtime/project_profile.py) | `_project_dependencies()` (L47-56) hace `tomllib.load(pyproject)` y lanza `ValueError("pyproject.toml is required...")` si no existe. `resolve_project_profile()` con `validate_dependencies=True` **falla sin pyproject**. Además `uv_sync_args()` (L193) y `uv_export_args()` (L204) generan comandos `uv` que ya no existirán. |
| [scripts/run_uv_sync.py](../../scripts/run_uv_sync.py) | Wrapper entero sobre `uv` (init/update/reset/ci). Todo su cuerpo (`uv_command_prefix`, `uv lock`, `uv sync`) queda sin binario. **Inoperable.** |
| [scripts/hooks/sync_dependencies.py](../../scripts/hooks/sync_dependencies.py) | Hashea `pyproject.toml` + `uv.lock` (L27-28) y ejecuta `uv sync` (L44-53). Sin esos archivos ni `uv`, **falla**. |
| [scripts/package.py](../../scripts/package.py) | `runtime_requirements_text()` (L26-36) ejecuta `uv export` para generar el `requirements.txt` del bundle. Sin `uv`, **no puede empaquetar**. |
| [scripts/restore_project.py](../../scripts/restore_project.py) | Importa `run_update` de `run_uv_sync` (L23) y comprueba `pyproject.toml` (L40). **Falla en cadena.** |

### 1.2 Scripts de entorno (setup / update de `.venv`)

| Archivo | Qué se rompe |
|---|---|
| [scripts/linux/setup_env.sh](../../scripts/linux/setup_env.sh) | L117-133: resuelve `uv`, exige `pyproject.toml`, llama `run_uv_sync.py init`. |
| [scripts/linux/update_venv.sh](../../scripts/linux/update_venv.sh) | L127-143: idéntico patrón para `update`. |
| [scripts/windows/setup_env.ps1](../../scripts/windows/setup_env.ps1) | L168-239: `Resolve-UvCommand`, exige `pyproject.toml`, `run_uv_sync.py init`, `UV_LINK_MODE`. |
| [scripts/windows/update_venv.ps1](../../scripts/windows/update_venv.ps1) | L177-237: mismo patrón para `update`. |

Todos estos **crean/sincronizan el `.venv` vía `uv`**. Con `pip`, la lógica de
creación de entorno cambia por completo (`python -m venv` + `pip install -r`).

### 1.3 Orquestación

| Archivo | Qué se rompe |
|---|---|
| [Makefile](../../Makefile) | Se elimina por decisión. **Todos** sus targets (`init`, `sync`, `uv-*`, `package`, `lint`, `fmt`, `test`, `test-cloud`, `clean`, `ai-refresh`, `restore`) desaparecen como superficie de comandos. Cualquier flujo que hoy dependa de `make X` queda sin punto de entrada. |
| [scripts/windows/run_make.ps1](../../scripts/windows/run_make.ps1) | Wrapper para localizar/ejecutar `make.exe`. Sin Makefile **pierde su propósito** por completo. |
| [.pre-commit-config.yaml](../../.pre-commit-config.yaml) | El hook `sync-dependencies` se dispara ante cambios en `pyproject.toml`/`uv.lock`/`ai/capabilities/*.yaml` y ejecuta `sync_dependencies.py` (que usa `uv`). **El hook se romperá** al ejecutarse. El hook `ai-refresh` no depende de uv, pero convive en el mismo archivo. |

### 1.4 Instalador (plantilla-como-producto)

| Archivo | Qué se rompe |
|---|---|
| [ai/installer.py](../../ai/installer.py) | `framework_version()` (L177-183) **lee la versión desde `pyproject.toml`**; sin él, `RuntimeError`. `_merge_pyproject()` / `_extract_toml_section()` (L578-644) usan `tomllib` para mergear pyproject en hosts. `APPEND_ONLY_FILES` y `EXCLUDED_EXACT_FILES` listan `pyproject.toml`/`uv.lock`. La máquina de instalación asume estos archivos. |

---

## 2. Referencias a actualizar

Menciones que **no rompen ejecución** pero quedan desactualizadas / engañosas y
deben corregirse para coherencia del framework educativo.

### 2.1 Documentación de usuario (alta prioridad — es lo que lee el estudiante)

| Archivo | Referencias |
|---|---|
| [README.md](../../README.md) | Menciona `make package/test/ai-refresh`, `uv`, `pyproject.toml`+`uv.lock`, "Dependency Model" basado en `uv`, wrappers `setup_env`/`update_venv`, sección "Linux/Windows Workflow" con `make uv-init`. Prácticamente toda la sección operativa. |
| [docs/linux_setup/README.md](../../docs/linux_setup/README.md) | Flujo `uv` + `make`. |
| [docs/linux_setup/uv_install.md](../../docs/linux_setup/uv_install.md) | Documento entero sobre instalar `uv`. |
| [docs/linux_setup/make_cheatlist.md](../../docs/linux_setup/make_cheatlist.md) | Cheatsheet de targets `make`. |
| [docs/windows_setup/README.md](../../docs/windows_setup/README.md) | Flujo `make` + `run_make.ps1` + `uv`. |
| [docs/windows_setup/uv_install.md](../../docs/windows_setup/uv_install.md) | Instalación de `uv`. |
| [docs/windows_setup/make_install.md](../../docs/windows_setup/make_install.md) | Instalación de `make`. |
| [docs/windows_setup/make_cheatlist.md](../../docs/windows_setup/make_cheatlist.md) | Cheatsheet de `make`. |
| [docs/windows_setup/template_versioning.md](../../docs/windows_setup/template_versioning.md) | Referencia a `uv`/versión. |
| [docs/workaround-python314-ssl-boto3.md](../../docs/workaround-python314-ssl-boto3.md) | Menciona `pyproject.toml` (extra cloud/truststore). |

### 2.2 Contrato de agente y configuración

| Archivo | Referencias |
|---|---|
| [AGENTS.md](../../AGENTS.md) | Sección "Package Manager Awareness" declara `uv` como gestor; "Execution Rules" recomienda `make <target>` y el flujo `run_make.ps1`. **Contradice la nueva decisión** — hay que reescribir estas secciones. |
| [.claude/settings.json](../../.claude/settings.json) | `permissions.allow` incluye `Bash(make test/lint/fmt/package/...)`, `Bash(uv run/sync/lock:*)`. Quedarán permisos huérfanos (no rompen, pero sobran). |
| [.gitattributes](../../.gitattributes) | Línea `Makefile text eol=lf` quedará sin objeto. |
| [.gitignore](../../.gitignore) | Ignora `.venv/`; con pip probablemente se mantiene, pero conviene revisar si hay que añadir/quitar patrones (p. ej. dejará de existir `uv.lock`). |

### 2.3 Capacidades y runtime (acoplamiento al modelo extras/groups)

| Archivo | Referencias |
|---|---|
| [ai/capabilities/languages/python.yaml](../../ai/capabilities/languages/python.yaml), [cloud/aws.yaml](../../ai/capabilities/cloud/aws.yaml), [business/saas.yaml](../../ai/capabilities/business/saas.yaml), [databases/supabase.yaml](../../ai/capabilities/databases/supabase.yaml) | Declaran `dependencies.extras` / `dependencies.groups` que son **conceptos de pyproject**. Sin pyproject, estos campos no tienen destino: hay que redefinir cómo una capacidad aporta dependencias (p. ej. un `requirements-<cap>.txt`). |
| [ai/runtime/project_profile.py](../../ai/runtime/project_profile.py) | Aunque se rompe (sección 1), si se quiere conservar el sistema de capacidades hay que **reescribir** `_project_dependencies`, `uv_sync_args`, `uv_export_args` para el modelo pip/requirements. |
| [ai/tools/inspect_project.py](../../ai/tools/inspect_project.py) | L131, L158: trata `pyproject.toml` como señal de proyecto Python al escanear librerías de datos. Debe pasar a mirar `requirements*.txt` (o ambos). No rompe, pero deja de detectar la señal. |
| [ai/domains/python.md](../../ai/domains/python.md) | Menciona `uv`/`pyproject` en la guía de dominio Python. |

### 2.4 Guía IA (skills y specs — prosa, menor prioridad)

Contienen menciones incidentales a `uv`/`make`/`pyproject` que conviene alinear
para no enseñar el flujo antiguo:
`ai/skills/aws/aws_smoke_testing.md`, `ai/skills/aws/lambda_packaging.md`,
`ai/skills/python/logging_structured.md`, `ai/skills/quality/simplicity.md`,
`ai/skills/docs/doc_review.md`, `ai/skills/terraform/terraform_orchestration.md`,
`ai/domains/terraform.md`, `docs/adr/0001-*.md`, `docs/adr/0002-lambda-packaging-strategy.md`,
`artifacts/README.md`.

> Los `specs/rework/*` (ADR-FW/SPEC-FW) también mencionan `uv`/`make`, pero son
> historia de diseño del framework original; ver sección 3.

---

## 3. Archivos que pueden eliminarse

Archivos cuya **razón de ser desaparece** con la migración.

### 3.1 Eliminación directa (quedan sin propósito)

| Archivo | Motivo |
|---|---|
| `Makefile` | Decisión explícita. |
| `pyproject.toml` | Decisión explícita. |
| `uv.lock` | Decisión explícita. |
| [scripts/run_uv_sync.py](../../scripts/run_uv_sync.py) | Wrapper de `uv` sin sustituto. |
| [scripts/hooks/sync_dependencies.py](../../scripts/hooks/sync_dependencies.py) | Hook basado en `uv` + hash de pyproject/uv.lock. |
| [scripts/windows/run_make.ps1](../../scripts/windows/run_make.ps1) | Localizador de `make.exe`; sin Makefile no aplica. |
| [docs/linux_setup/uv_install.md](../../docs/linux_setup/uv_install.md) | Instala `uv`. |
| [docs/linux_setup/make_cheatlist.md](../../docs/linux_setup/make_cheatlist.md) | Targets `make`. |
| [docs/windows_setup/uv_install.md](../../docs/windows_setup/uv_install.md) | Instala `uv`. |
| [docs/windows_setup/make_install.md](../../docs/windows_setup/make_install.md) | Instala `make`. |
| [docs/windows_setup/make_cheatlist.md](../../docs/windows_setup/make_cheatlist.md) | Cheatsheet `make`. |

### 3.2 Eliminación **condicionada** a reescritura (no borrar sin sustituto)

| Archivo | Condición |
|---|---|
| [scripts/{linux,windows}/setup_env.*](../../scripts/) y `update_venv.*` | Solo eliminables si se sustituyen por un equivalente `python -m venv` + `pip install -r requirements.txt`. Su **función** (bootstrap del entorno) sigue siendo necesaria. |
| [scripts/package.py](../../scripts/package.py) | La función (bundle de despliegue) sigue siendo útil; hay que reescribir la generación del `requirements.txt` sin `uv export`. |
| [scripts/restore_project.py](../../scripts/restore_project.py) | Depende de `run_uv_sync`; eliminar o reescribir. |

### 3.3 Candidatos por contexto educativo (no por la migración, pero relevantes)

- `specs/rework/*` (ADR-FW / SPEC-FW / SPEC-FW-IMPL-PLAN) — historia del rediseño
  del motor; alto ruido para estudiantes. Eliminables sin afectar ejecución.
- `docs/windows_setup/template_versioning.md` — ligado al modelo de versión
  leído desde pyproject.

---

## 4. Configuración que debe simplificarse

| Área | Estado actual | Simplificación pendiente |
|---|---|---|
| **Modelo de dependencias** | `pyproject.toml` con 4 extras + 2 dependency-groups, resueltos por `uv` desde `uv.lock`. | Un (o varios) `requirements.txt` planos instalables con `pip install -r`. Decidir si se mantiene la separación por capacidad (p. ej. `requirements.txt` base + `requirements-cloud.txt`) o un único archivo. |
| **Sistema de capacidades → dependencias** | Capacidades declaran `extras`/`groups` que `project_profile.py` valida contra pyproject. | Redefinir el vínculo capacidad→dependencias hacia requirements, o **desacoplar** capacidades de la instalación de paquetes (para enseñanza, quizá basta un requirements único). |
| **Config de pytest/ruff** | Viven en `[tool.pytest.ini_options]` y (según skills) `[tool.ruff]` **dentro de pyproject**. | Al borrar pyproject, migrar a `pytest.ini`/`setup.cfg`/`ruff.toml` o `tox.ini`. **Si no se migra, `pytest` y `ruff` pierden su configuración.** |
| **Versión del framework** | `framework_version()` la lee de `pyproject.toml`. | Mover la versión a otro archivo (p. ej. `VERSION`, `__init__.py`) o eliminar el versionado si el instalador deja de usarse. |
| **pre-commit** | Dos hooks; `sync-dependencies` acoplado a uv. | Quitar/reescribir `sync-dependencies`; conservar `ai-refresh` si sigue teniendo sentido. Revisar `additional_dependencies` (usa `pyyaml`). |
| **`.claude/settings.json`** | Permisos `make *` y `uv *`. | Reemplazar por permisos `pip`/`python -m venv`/`pytest`/`ruff` directos. |
| **`.gitattributes` / `.gitignore`** | `Makefile eol=lf`; ignora `.venv/`. | Quitar la regla de `Makefile`; validar patrones ignore (ya no habrá `uv.lock`). |
| **AGENTS.md** | "Package Manager Awareness: usa uv"; "Execution Rules: make". | Reescribir ambas secciones al modelo pip; hoy **contradicen** la decisión tomada. |
| **Instaladores** | `ai/installer.py` trata pyproject como append-only y lee versión de él. | Decidir si el instalador sigue existiendo en la variante educativa; si sí, desacoplarlo de pyproject/uv.lock. |

---

## 5. Riesgos de la migración

Ordenados por impacto.

1. **Pérdida de resolución determinista (lockfile).**
   `uv.lock` fija versiones transitivas exactas. Un `requirements.txt` sin pins
   completos (`pip freeze`) introduce **builds no reproducibles** entre máquinas
   de estudiantes — justo lo contrario del principio "reproducible" del repo.
   *Mitigación a considerar:* `requirements.txt` con versiones pineadas.

2. **El sistema de capacidades queda huérfano.**
   Es el núcleo diferenciador del framework y está construido sobre
   `extras`/`groups` de pyproject. Migrar a pip obliga a **rediseñar o retirar**
   esa capa completa (`project_profile.py`, descriptores `ai/capabilities/*.yaml`,
   filtrado de skills por dependencias). Riesgo de romper `refresh_context.py`,
   `restore_project.py` y la generación `.ai/` en cascada.

3. **Configuración de tooling perdida silenciosamente.**
   Si se borra pyproject sin migrar `[tool.pytest]` y `[tool.ruff]`, `pytest`
   corre sin sus markers (`cloud`) y `ruff` sin sus reglas — **fallos sutiles**,
   no errores ruidosos. Alto riesgo de pasar desapercibido.

4. **Fallo del instalador (plantilla-como-producto).**
   `framework_version()` lanza `RuntimeError` sin pyproject; los merges
   append-only asumen pyproject/uv.lock. Si el instalador sigue vivo, **se rompe
   en el arranque**. Si se retira, hay que decidir cómo se distribuye la variante
   educativa.

5. **Ruptura en cadena por imports.**
   `restore_project.py` importa de `run_uv_sync.py`; `package.py` y
   `sync_dependencies.py` importan `uv_*_args` de `project_profile.py`. Borrar un
   módulo sin ajustar los importadores provoca `ImportError` en múltiples flujos.

6. **pre-commit rompe el commit.**
   Mientras `sync-dependencies` siga en `.pre-commit-config.yaml`, **cada commit**
   intentará ejecutar `uv` y fallará, bloqueando el trabajo hasta que se corrija.

7. **Divergencia doc-vs-realidad se amplía.**
   Toda la documentación de setup (Windows/Linux) enseña el flujo antiguo. Si se
   migra el código pero no los docs, los estudiantes seguirán instrucciones que
   ya no funcionan — el peor escenario para un framework de enseñanza.

8. **Windows sin `uv`/`make`: los mitigantes desaparecen.**
   `run_uv_sync.py` maneja `UV_LINK_MODE=copy` para OneDrive y estados de `.venv`
   bloqueado; `run_make.ps1` resuelve `make.exe` en entornos corporativos. Al
   migrar hay que **reproducir esas mitigaciones** en el nuevo flujo pip, o los
   alumnos en Windows/OneDrive encontrarán los errores que hoy están resueltos.

---

## Resumen ejecutivo

- **La migración no es cosmética.** Cambiar comandos (`make`→scripts, `uv`→`pip`)
  es lo fácil; lo difícil es que **el sistema de capacidades y la generación de
  contexto IA están construidos sobre el modelo `extras`/`groups` de
  `pyproject.toml`**, que pip no tiene.
- **5 módulos Python se rompen** (`project_profile.py`, `run_uv_sync.py`,
  `sync_dependencies.py`, `package.py`, `restore_project.py`) más 4 scripts de
  entorno y el instalador.
- **Configuración a rescatar antes de borrar pyproject:** `[tool.pytest]` y
  `[tool.ruff]` (o se pierden en silencio) y la versión del framework.
- **Riesgo principal:** perder reproducibilidad (lockfile) y romper pre-commit /
  instalador en cadena; secundario, dejar la documentación enseñando el flujo
  viejo.

*Fin del informe. Sin cambios implementados, según lo solicitado.*
