# Hallazgos de la implementación — migración a `pip` + `requirements.txt`

> Complementa [migracion-pip-requirements.md](migracion-pip-requirements.md)
> (diagnóstico previo, sin cambios) con lo realmente ejecutado en el branch
> `curso`. Alcance de la migración: retirar el sistema de capacidades por
> completo, incluir el instalador (`ai/installer.py`), y usar versiones
> pineadas en `requirements.txt` (base + `local` + `cloud`).

---

## 1. Qué se eliminó

| Archivo/directorio | Motivo |
|---|---|
| `Makefile` | Decisión explícita del usuario. |
| `pyproject.toml`, `uv.lock` | Decisión explícita del usuario. |
| `ai/runtime/project_profile.py` | Resolvía extras/groups desde pyproject; sin objeto sin capacidades. |
| `ai/runtime/capability_registry.py` | Cargaba descriptores de `ai/capabilities/`; directorio eliminado. |
| `ai/runtime/profile.py` | Parseaba `.template-profile.yaml`; archivo eliminado. |
| `ai/capabilities/` (8 descriptores YAML) | El modelo de capacidades se retiró; las skills ahora están siempre activas. |
| `.template-profile.yaml` | Ya no hay perfil de capacidades que persistir. |
| `scripts/run_uv_sync.py` | Wrapper de `uv sync`/`uv lock`; sin sustituto 1:1 (pip no tiene lockfile nativo). |
| `scripts/hooks/sync_dependencies.py` | Hook de pre-commit que ejecutaba `uv sync`; el hook `sync-dependencies` se quitó de `.pre-commit-config.yaml`. |
| `scripts/windows/run_make.ps1` | Localizador de `make.exe`; sin Makefile no aplica. |
| `docs/{linux,windows}_setup/uv_install.md`, `make_install.md`, `make_cheatlist.md` | Documentaban instalación/uso de herramientas retiradas. |
| `tests/test_capability_registry.py`, `test_profile.py`, `test_project_profile.py`, `test_sync_dependencies.py` | Testeaban exclusivamente los módulos eliminados arriba. |

## 2. Qué se creó

| Archivo | Contenido |
|---|---|
| `requirements.txt` | Dependencias de runtime pineadas (`==`), extraídas de `uv.lock`: sección base + `local` + `cloud` (decisión confirmada por el usuario). |
| `requirements-dev.txt` | Dependencias de desarrollo pineadas (equivalente al antiguo `dev-local`: pytest, ruff, pre-commit, hypothesis, httpx, faker). |
| `pytest.ini` | Rescata el único ajuste de tooling que vivía en pyproject: el marker `cloud` de `[tool.pytest.ini_options]`. Ruff no tenía configuración propia en pyproject (corría con defaults), así que no requirió rescate. |
| `VERSION` | Sustituye a `[project].version` de pyproject como fuente de `framework_version()` en el instalador. |

## 3. Qué se reescribió (no solo renombrado)

- **`ai/runtime/skill_registry.py`**: se quitó el filtrado de skills por capacidad activa (`_filter_active_skills`, `active_paths`). `build_skills_registry` ahora devuelve siempre el catálogo completo de `ai/skills.yaml`.
- **`ai/runtime/context_bundle.py`** y **`ai/tools/refresh_context.py`**: perdieron el parámetro `resolved`/`ResolvedProfile`; `refresh_context` genera siempre los cuatro artefactos (antes dependía de qué `artifacts` declarara la capacidad activa).
- **`ai/runtime/dependency_graph.py`**: `active_scanners()` (que resolvía el perfil de capacidades) se eliminó; `build_dependency_graph` cae directamente a `DEFAULT_SCANNERS = ["python"]` si no se pasan scanners explícitos.
- **`ai/tools/inspect_project.py`**: la señal de "hay un proyecto Python empaquetable" pasó de `pyproject.toml` a cualquier archivo `requirements*.txt`.
- **`scripts/package.py`**: en vez de invocar `uv export` para resolver requirements dinámicamente por capacidad, copia `requirements.txt` tal cual al bundle (ya no hay capacidades que resolver).
- **`scripts/restore_project.py`**: su primer paso pasó de "resolver perfil + `uv sync`" a "`pip install -r requirements.txt -r requirements-dev.txt`" vía subprocess directo.
- **`scripts/{linux,windows}/setup_env.*`, `update_venv.*`**: reescritos a `python -m venv` + `pip install`, conservando la estructura de resolución de intérprete (funciones `resolve_python_command`/`New-CommandSpec` en PowerShell) pero sin las ramas de `uv`/OneDrive `UV_LINK_MODE`.
- **`ai/installer.py`** (~1200 → ~950 líneas): se eliminó toda la maquinaria de selección de capacidades (`prompt_enabled_capabilities`, `validate_enabled_capabilities`, `capability_selection`, `available_capability_ids`), el renderizado de `.template-profile.yaml` (`render_target_file`, `profile_document`), y el merge de secciones TOML (`_merge_pyproject`, `_extract_toml_section`, `tomllib`). El merge append-only ahora solo aplica a `.pre-commit-config.yaml`. `framework_version()` lee de `VERSION` en vez de parsear pyproject con regex.
- **`install_windows.py`/`install_linux.py`**: se quitaron los flags `--enable`, `--saas` y la resolución de capacidades del CLI.

## 4. Tests actualizados (no solo los que se borraron)

- **`tests/test_installer.py`**: reescrito sin `enabled_capabilities`/`validate_enabled_capabilities`/`text_sha256` (esta última función se eliminó del instalador por no tener más uso). Se sustituyeron las aserciones sobre `pyproject.toml`/`.template-profile.yaml`/`uv.lock` por aserciones sobre `requirements.txt`/`requirements-dev.txt`.
- **`tests/test_install_entrypoints.py`**: se quitaron los tests de `--enable`/selección interactiva de capacidades; se mantuvo la cobertura de dry-run, update, y auto-detección de instalación previa.
- **`tests/test_script_wrappers.py`**: se quitaron los tests de `run_uv_sync.py`; se añadió un test de `scripts/package.py` que verifica que el bundle incluye `requirements.txt` copiado (no generado dinámicamente).
- **`tests/test_dependency_graph.py`**: se quitaron los dos tests de `active_scanners` basados en capacidades; se añadió un test que confirma el fallback a `DEFAULT_SCANNERS`.
- **`tests/test_restore_project.py`**: reescrito por completo — el original testeaba el filtrado de skills por capacidad (`enable_saas=True/False`), que ya no existe. Los nuevos tests verifican que **todas** las skills declaradas se incluyen siempre y que la instalación de dependencias se salta quietamente cuando no hay `requirements*.txt`.
- **`tests/test_refresh_context.py`**: no requirió cambios — ya no dependía de capacidades.

## 5. Qué se dejó fuera de alcance (decisión consciente)

- **`specs/rework/*` (ADR-FW, SPEC-FW)**: menciones históricas a `uv`/`make`/pyproject se dejaron intactas. Son documentos que narran decisiones de diseño del framework en su momento — reescribirlos retroactivamente falsificaría la historia. Si se quiere reducir ruido para estudiantes, es una limpieza aparte (ya señalada en el diagnóstico original).
- **`docs/adr/0002-lambda-packaging-strategy.md`**: mismo criterio — es un ADR del proyecto que documenta una decisión con su contexto de la época (incluye referencias a líneas concretas de `pyproject.toml`/`Makefile`/`run_uv_sync.py` que ya no existen). Se conserva como registro histórico.

## 6. Verificación pendiente de ejecutar

No se ha corrido `pip install` real ni la suite de tests contra un entorno limpio en esta sesión (ver plan, sección "Verificación"). Antes de dar la migración por cerrada, ejecutar:

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt -r requirements-dev.txt   # Windows
python -m pytest
python -m ruff check ai scripts tests
python scripts/hooks/ai_refresh.py
python scripts/package.py
```
