from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai.runtime.config import (
    entrypoint_roots,
    ignore_dirs,
    ignore_top_level_files,
    load_context_config,
    module_roots,
)


VERSION = "0.2.0"
DATA_LIBRARIES = {"awswrangler", "duckdb", "pandas", "polars", "pyarrow"}
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z0-9_\.]+)", re.MULTILINE)


def _safe_read(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return ""


def is_ignored_path(
    path: Path, project_root: Path, config: dict[str, Any] | None = None
) -> bool:
    config = config or load_context_config(project_root)
    relative = path.relative_to(project_root)
    ignored_directory_names = ignore_dirs(config)
    ignored_top_level = ignore_top_level_files(config)

    if any(part in ignored_directory_names for part in relative.parts):
        return True
    if relative.name in ignored_top_level and len(relative.parts) == 1:
        return True
    if any(part.startswith(".") and part not in {".github"} for part in relative.parts):
        return True
    return False


def iter_project_files(project_root: Path) -> list[Path]:
    config = load_context_config(project_root)
    files: list[Path] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if is_ignored_path(path, project_root, config):
            continue
        files.append(path)
    return files


def _rel(path: Path, project_root: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()


JS_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}


def _detect_languages(project_root: Path, files: list[Path]) -> dict[str, Any]:
    counts = Counter()
    languages: set[str] = set()

    for path in files:
        suffix = path.suffix.lower()
        if suffix == ".py":
            languages.add("python")
            counts["python"] += 1
        elif suffix == ".sql":
            languages.add("sql")
            counts["sql"] += 1
        elif suffix == ".tf":
            languages.add("terraform")
            counts["terraform"] += 1
        elif suffix in JS_SUFFIXES:
            languages.add("javascript")
            counts["javascript"] += 1
        elif suffix == ".go":
            languages.add("go")
            counts["go"] += 1
        elif suffix == ".rs":
            languages.add("rust")
            counts["rust"] += 1

    primary_language = None
    for candidate in ("python", "sql", "terraform", "javascript", "go", "rust"):
        if counts[candidate]:
            primary_language = candidate
            break

    has_package_json = any(path.name == "package.json" for path in files)

    project_types: set[str] = set()
    if primary_language == "python":
        project_types.add("automation")
    if counts["sql"] or (project_root / "src" / "transformations").exists():
        project_types.add("data")
    if counts["terraform"] or (project_root / "infra").exists():
        project_types.add("infrastructure")
    if counts["javascript"] and has_package_json:
        project_types.add("frontend")
    if counts["go"] or counts["rust"]:
        project_types.add("service")
    if not project_types:
        project_types.add("unknown")

    return {
        "project": {
            "name": project_root.name,
            "primary_language": primary_language,
            "languages": sorted(languages),
            "project_types": sorted(project_types),
        },
        "structure": {
            "has_tests": (project_root / "tests").exists(),
            "has_terraform": counts["terraform"] > 0
            or (project_root / "infra").exists(),
            "has_sql": counts["sql"] > 0,
            "has_guidance": (project_root / "ai" / "skills").exists(),
        },
    }


def _detect_data_stack(project_root: Path, files: list[Path]) -> dict[str, Any]:
    libraries: set[str] = set()
    patterns: set[str] = set()

    for path in files:
        rel_path = _rel(path, project_root)
        lower_rel = rel_path.lower()

        if path.suffix.lower() == ".sql":
            patterns.add("sql")
        if any(token in lower_rel for token in ("job", "pipeline", "etl", "transform")):
            patterns.add("etl")
        if any(token in lower_rel for token in ("contract", "validation", "quality")):
            patterns.add("data_quality")

        if not path.name.startswith("requirements") and path.suffix.lower() != ".py":
            continue

        text = _safe_read(path).lower()
        for library in DATA_LIBRARIES:
            if library in text:
                libraries.add(library)

    return {
        "data_stack": {
            "libraries": sorted(libraries),
            "patterns": sorted(patterns),
        }
    }


JS_FRAMEWORKS = {
    "react": "react",
    "next": "nextjs",
}
JS_BUILD_TOOLS = {
    "vite": "vite",
}


def _detect_js_stack(project_root: Path, files: list[Path]) -> dict[str, Any]:
    frameworks: set[str] = set()
    build_tools: set[str] = set()

    for path in files:
        if path.name != "package.json":
            continue

        try:
            manifest = json.loads(_safe_read(path))
        except json.JSONDecodeError:
            continue
        if not isinstance(manifest, dict):
            continue

        dependency_names: set[str] = set()
        for key in ("dependencies", "devDependencies"):
            deps = manifest.get(key)
            if isinstance(deps, dict):
                dependency_names.update(deps.keys())

        for package_name, framework in JS_FRAMEWORKS.items():
            if package_name in dependency_names:
                frameworks.add(framework)
        for package_name, build_tool in JS_BUILD_TOOLS.items():
            if package_name in dependency_names:
                build_tools.add(build_tool)

    return {
        "js_stack": {
            "frameworks": sorted(frameworks),
            "build_tools": sorted(build_tools),
        }
    }


def _detect_go_rust_stack(project_root: Path) -> dict[str, Any]:
    go_module = None
    go_mod_path = project_root / "go.mod"
    if go_mod_path.exists():
        match = re.search(r"^\s*module\s+(\S+)", _safe_read(go_mod_path), re.MULTILINE)
        go_module = match.group(1) if match else None

    rust_crates: list[str] = []
    cargo_toml_path = project_root / "Cargo.toml"
    if cargo_toml_path.exists():
        import tomllib

        try:
            cargo_doc = tomllib.loads(_safe_read(cargo_toml_path))
        except tomllib.TOMLDecodeError:
            cargo_doc = {}
        package_name = (cargo_doc.get("package") or {}).get("name")
        if package_name:
            rust_crates.append(str(package_name))

    return {
        "go_stack": {"module": go_module},
        "rust_stack": {"crates": sorted(rust_crates)},
    }


def _detect_cloud(project_root: Path, files: list[Path]) -> dict[str, Any]:
    providers: set[str] = set()
    infra_tools: set[str] = set()

    if (project_root / "infra").exists():
        infra_tools.add("terraform")

    for path in files:
        suffix = path.suffix.lower()
        if suffix not in {
            ".py",
            ".tf",
            ".yaml",
            ".yml",
            ".json",
        } and not path.name.startswith("requirements"):
            continue

        text = _safe_read(path).lower()
        if suffix == ".tf":
            infra_tools.add("terraform")
        if (
            'provider "aws"' in text
            or "arn:aws:" in text
            or "boto3" in text
            or "awswrangler" in text
            or "@aws-sdk/" in text
            or '"aws-sdk"' in text
        ):
            providers.add("aws")

    return {
        "cloud": {
            "providers": sorted(providers),
            "infra_tools": sorted(infra_tools),
        }
    }


def _python_files_under(
    project_root: Path, relative_dir: str, config: dict[str, Any]
) -> list[Path]:
    base = project_root / relative_dir
    if not base.exists():
        return []

    paths: list[Path] = []
    for path in sorted(base.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        if is_ignored_path(path, project_root, config):
            continue
        paths.append(path)
    return paths


def _files_from_roots(
    project_root: Path,
    files: list[str],
    directories: list[str],
    config: dict[str, Any],
) -> list[Path]:
    resolved: list[Path] = []

    for relative_file in files:
        path = project_root / relative_file
        if (
            path.exists()
            and path.is_file()
            and not is_ignored_path(path, project_root, config)
        ):
            resolved.append(path)

    for relative_dir in directories:
        resolved.extend(_python_files_under(project_root, relative_dir, config))

    return resolved


def _entrypoints(project_root: Path) -> list[dict[str, str]]:
    config = load_context_config(project_root)
    roots = entrypoint_roots(config)
    entrypoints: list[dict[str, str]] = []

    for path in _files_from_roots(
        project_root, roots["files"], roots["directories"], config
    ):
        relative = path.relative_to(project_root).as_posix()
        kind = (
            "job"
            if "jobs/" in relative
            else "cli"
            if relative == "main.py"
            else "script"
        )
        entrypoints.append({"type": kind, "path": relative})

    return entrypoints


def _core_modules(project_root: Path) -> list[dict[str, str]]:
    config = load_context_config(project_root)
    roots = module_roots(config)
    modules = [
        {"path": path.relative_to(project_root).as_posix()}
        for path in _files_from_roots(
            project_root, roots["files"], roots["directories"], config
        )
    ]
    return modules[:15]


def inspect_project(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    files = iter_project_files(project_root)
    language_info = _detect_languages(project_root, files)
    data_info = _detect_data_stack(project_root, files)
    cloud_info = _detect_cloud(project_root, files)
    js_info = _detect_js_stack(project_root, files)
    go_rust_info = _detect_go_rust_stack(project_root)

    return {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "project": language_info["project"],
        "structure": language_info["structure"],
        "data_stack": data_info["data_stack"],
        "js_stack": js_info["js_stack"],
        "go_stack": go_rust_info["go_stack"],
        "rust_stack": go_rust_info["rust_stack"],
        "cloud": cloud_info["cloud"],
        "entrypoints": _entrypoints(project_root),
        "core_modules": _core_modules(project_root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a project for AI context signals."
    )
    parser.add_argument("--project-root", default=".", help="Project root to inspect.")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output."
    )
    args = parser.parse_args()

    payload = inspect_project(Path(args.project_root))
    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
