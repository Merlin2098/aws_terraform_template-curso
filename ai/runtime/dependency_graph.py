from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ai.tools.inspect_project import is_ignored_path


VERSION = "0.2.0"

DEFAULT_SCANNERS = ["python", "javascript", "go", "rust"]


@dataclass
class Node:
    id: str
    kind: str
    label: str
    module: str | None = None
    file_path: str | None = None


@dataclass
class Edge:
    source: str
    target: str
    kind: str
    raw: str
    lineno: int | None = None


@dataclass
class ScannerResult:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)


ScannerFn = Callable[[Path], ScannerResult]


def _safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _iter_files(project_root: Path, pattern: str) -> list[Path]:
    files: list[Path] = []
    for path in project_root.rglob(pattern):
        if is_ignored_path(path, project_root):
            continue
        files.append(path)
    return files


def _module_name(project_root: Path, path: Path) -> str:
    rel = path.relative_to(project_root).as_posix()
    if rel == "main.py":
        return "main"
    if rel.endswith("/__init__.py"):
        return rel[: -len("/__init__.py")].replace("/", ".")
    if rel == "__init__.py":
        return "__init__"
    return rel[:-3].replace("/", ".")


def _pick_internal(imported: str, modules: set[str]) -> str | None:
    if imported in modules:
        return imported
    parts = imported.split(".")
    for index in range(len(parts) - 1, 0, -1):
        candidate = ".".join(parts[:index])
        if candidate in modules:
            return candidate
    return None


def scan_python(project_root: Path) -> ScannerResult:
    """Build Python module/import nodes and edges via the ``ast`` module."""
    files = _iter_files(project_root, "*.py")
    module_to_file = {
        _module_name(project_root, path): path.relative_to(project_root).as_posix()
        for path in files
    }
    modules = set(module_to_file)
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    issues: list[dict[str, str]] = []

    for module, rel_path in module_to_file.items():
        nodes[f"module:{module}"] = Node(
            id=f"module:{module}",
            kind="python_module",
            label=module,
            module=module,
            file_path=rel_path,
        )

    for module, rel_path in module_to_file.items():
        path = project_root / rel_path
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
        except Exception as exc:
            issues.append({"file": rel_path, "message": str(exc)})
            continue

        source = f"module:{module}"
        for node in ast.walk(tree):
            imports: list[tuple[str, int | None]] = []
            if isinstance(node, ast.Import):
                imports = [
                    (alias.name, getattr(node, "lineno", None)) for alias in node.names
                ]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports = [(node.module, getattr(node, "lineno", None))]

            for imported, lineno in imports:
                internal = _pick_internal(imported, modules)
                if internal:
                    target = f"module:{internal}"
                else:
                    package = imported.split(".")[0]
                    target = f"external:{package}"
                    nodes.setdefault(
                        target,
                        Node(
                            id=target,
                            kind="external_package",
                            label=package,
                            module=package,
                        ),
                    )
                edges.append(
                    Edge(
                        source=source,
                        target=target,
                        kind="imports",
                        raw=imported,
                        lineno=lineno,
                    )
                )

    return ScannerResult(nodes=list(nodes.values()), edges=edges, issues=issues)


JS_EXTENSIONS = ("*.js", "*.jsx", "*.ts", "*.tsx")

# Matches `import ... from "x"`, `import "x"`, and `require("x")`.
JS_IMPORT_RE = re.compile(
    r"""(?:
        import\s+(?:[^'"]*?\sfrom\s+)?['"](?P<from>[^'"]+)['"]
        |
        require\(\s*['"](?P<require>[^'"]+)['"]\s*\)
    )""",
    re.VERBOSE,
)


def _js_module_name(project_root: Path, path: Path) -> str:
    rel = path.relative_to(project_root).as_posix()
    for suffix in (".tsx", ".ts", ".jsx", ".js"):
        if rel.endswith(suffix):
            rel = rel[: -len(suffix)]
            break
    if rel.endswith("/index"):
        rel = rel[: -len("/index")]
    return rel


def scan_javascript(project_root: Path) -> ScannerResult:
    """Build JS/TS module/import nodes and edges via regex-based import detection.

    No AST library is available for JS/TS in the Python stdlib, so imports are
    detected with a regex over ``import``/``require`` statements. Internal
    imports (relative paths) resolve to project modules; everything else is an
    external package, mirroring ``scan_python``'s node/edge shape.
    """
    files: list[Path] = []
    for pattern in JS_EXTENSIONS:
        files.extend(_iter_files(project_root, pattern))

    module_to_file = {
        _js_module_name(project_root, path): path.relative_to(project_root).as_posix()
        for path in files
    }
    modules = set(module_to_file)
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    issues: list[dict[str, str]] = []

    for module, rel_path in module_to_file.items():
        nodes[f"module:{module}"] = Node(
            id=f"module:{module}",
            kind="javascript_module",
            label=module,
            module=module,
            file_path=rel_path,
        )

    for module, rel_path in module_to_file.items():
        path = project_root / rel_path
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:
            issues.append({"file": rel_path, "message": str(exc)})
            continue

        source = f"module:{module}"
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in JS_IMPORT_RE.finditer(line):
                imported = match.group("from") or match.group("require")
                if not imported:
                    continue

                if imported.startswith("."):
                    base = (Path(rel_path).parent / imported).as_posix()
                    candidate = re.sub(r"/\./", "/", base)
                    while "/../" in candidate:
                        candidate = re.sub(r"[^/]+/\.\./", "", candidate, count=1)
                    candidate = candidate.lstrip("./")
                    internal = _pick_internal(candidate, modules) or _pick_internal(
                        f"{candidate}/index", modules
                    )
                    if internal:
                        target = f"module:{internal}"
                    else:
                        target = f"module:{candidate}"
                        nodes.setdefault(
                            target,
                            Node(id=target, kind="javascript_module", label=candidate),
                        )
                else:
                    package = imported.split("/")[0]
                    if package.startswith("@"):
                        parts = imported.split("/")
                        package = "/".join(parts[:2]) if len(parts) > 1 else package
                    target = f"external:{package}"
                    nodes.setdefault(
                        target,
                        Node(
                            id=target,
                            kind="external_package",
                            label=package,
                            module=package,
                        ),
                    )

                edges.append(
                    Edge(
                        source=source,
                        target=target,
                        kind="imports",
                        raw=imported,
                        lineno=lineno,
                    )
                )

    return ScannerResult(nodes=list(nodes.values()), edges=edges, issues=issues)


GO_MODULE_RE = re.compile(r"^\s*module\s+(\S+)", re.MULTILINE)
GO_IMPORT_BLOCK_RE = re.compile(r"import\s*\(([^)]*)\)", re.DOTALL)
GO_IMPORT_LINE_RE = re.compile(r"import\s+\"([^\"]+)\"")
GO_IMPORT_PATH_RE = re.compile(r"(?:\w+\s+)?\"([^\"]+)\"")


def _go_module_path(project_root: Path) -> str | None:
    go_mod = project_root / "go.mod"
    if not go_mod.exists():
        return None
    match = GO_MODULE_RE.search(_safe_read_text(go_mod))
    return match.group(1) if match else None


def _go_package_name(project_root: Path, path: Path) -> str:
    """Go packages are one per directory, not one per file."""
    rel_dir = path.relative_to(project_root).parent.as_posix()
    return "." if rel_dir == "." else rel_dir


def scan_go(project_root: Path) -> ScannerResult:
    """Build Go package/import nodes and edges via regex-based import detection.

    Go has no import-parsing library in the Python stdlib, so imports are
    detected with a regex over ``import (...)`` blocks and single-line
    ``import "..."`` statements. Unlike Python/JS, Go packages are one per
    *directory* — files sharing a directory collapse into a single node.
    """
    files = _iter_files(project_root, "*.go")
    module_root = _go_module_path(project_root)

    package_to_files: dict[str, list[str]] = {}
    for path in files:
        package = _go_package_name(project_root, path)
        package_to_files.setdefault(package, []).append(
            path.relative_to(project_root).as_posix()
        )

    packages = set(package_to_files)
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    issues: list[dict[str, str]] = []

    for package, rel_paths in package_to_files.items():
        nodes[f"module:{package}"] = Node(
            id=f"module:{package}",
            kind="go_module",
            label=package,
            module=package,
            file_path=sorted(rel_paths)[0],
        )

    for package, rel_paths in package_to_files.items():
        source = f"module:{package}"
        for rel_path in rel_paths:
            path = project_root / rel_path
            try:
                text = _safe_read_text(path)
            except Exception as exc:
                issues.append({"file": rel_path, "message": str(exc)})
                continue

            import_paths: list[tuple[str, int | None]] = []
            for block_match in GO_IMPORT_BLOCK_RE.finditer(text):
                block_start_line = text.count("\n", 0, block_match.start()) + 1
                for offset, line in enumerate(block_match.group(1).splitlines()):
                    path_match = GO_IMPORT_PATH_RE.search(line)
                    if path_match:
                        import_paths.append(
                            (path_match.group(1), block_start_line + offset)
                        )
            for lineno, line in enumerate(text.splitlines(), start=1):
                single_match = GO_IMPORT_LINE_RE.search(line)
                if single_match and "(" not in line:
                    import_paths.append((single_match.group(1), lineno))

            for imported, lineno in import_paths:
                internal_package = None
                if module_root and imported.startswith(module_root):
                    candidate = imported[len(module_root) :].lstrip("/")
                    if candidate in packages:
                        internal_package = candidate
                    elif candidate == "" and "." in packages:
                        internal_package = "."

                if internal_package is not None:
                    target = f"module:{internal_package}"
                else:
                    target = f"external:{imported}"
                    nodes.setdefault(
                        target,
                        Node(
                            id=target,
                            kind="external_package",
                            label=imported,
                            module=imported,
                        ),
                    )

                edges.append(
                    Edge(
                        source=source,
                        target=target,
                        kind="imports",
                        raw=imported,
                        lineno=lineno,
                    )
                )

    return ScannerResult(nodes=list(nodes.values()), edges=edges, issues=issues)


RUST_USE_RE = re.compile(r"use\s+((?:crate|self|super)(?:::\w+)*|\w[\w:]*)")
RUST_MOD_RE = re.compile(r"^\s*(?:pub\s+)?mod\s+(\w+)\s*;", re.MULTILINE)


def _rust_module_name(project_root: Path, path: Path) -> str:
    rel = path.relative_to(project_root).as_posix()
    if rel.endswith(".rs"):
        rel = rel[: -len(".rs")]

    parts = [part for part in rel.split("/") if part]
    stem = parts[-1] if parts else ""

    if stem == "mod":
        # foo/bar/mod.rs is the module foo::bar.
        parts = parts[:-1]
    elif stem in {"main", "lib"}:
        # <crate_root>/src/main.rs or lib.rs is the crate root itself,
        # regardless of how deep the "src" directory sits.
        parts = parts[:-1]
        if parts and parts[-1] == "src":
            parts = parts[:-1]
        else:
            parts = []

    return "::".join(parts) or "crate"


def scan_rust(project_root: Path) -> ScannerResult:
    """Build Rust module/import nodes and edges via regex-based import detection.

    Rust has no import-parsing library in the Python stdlib, so ``use``
    statements and ``mod`` declarations are detected with regexes. Internal
    modules resolve via ``crate::``/``self::``/``super::`` paths or declared
    ``mod`` names; everything else is treated as an external crate.
    """
    files = _iter_files(project_root, "*.rs")
    module_to_file = {
        _rust_module_name(project_root, path): path.relative_to(project_root).as_posix()
        for path in files
    }
    modules = set(module_to_file)
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    issues: list[dict[str, str]] = []

    for module, rel_path in module_to_file.items():
        nodes[f"module:{module}"] = Node(
            id=f"module:{module}",
            kind="rust_module",
            label=module,
            module=module,
            file_path=rel_path,
        )

    for module, rel_path in module_to_file.items():
        path = project_root / rel_path
        try:
            text = _safe_read_text(path)
        except Exception as exc:
            issues.append({"file": rel_path, "message": str(exc)})
            continue

        source = f"module:{module}"
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in RUST_MOD_RE.finditer(line):
                mod_name = match.group(1)
                candidate = f"{module}::{mod_name}" if module != "crate" else mod_name
                internal = _pick_internal(candidate, modules) or (
                    candidate if candidate in modules else None
                )
                target = f"module:{internal}" if internal else f"module:{candidate}"
                nodes.setdefault(
                    target, Node(id=target, kind="rust_module", label=candidate)
                )
                edges.append(
                    Edge(
                        source=source,
                        target=target,
                        kind="declares",
                        raw=mod_name,
                        lineno=lineno,
                    )
                )

            for match in RUST_USE_RE.finditer(line):
                imported = match.group(1)
                root_segment = imported.split("::")[0]

                if root_segment in {"crate", "self", "super"}:
                    internal = _pick_internal(imported, modules)
                    target = f"module:{internal}" if internal else f"module:{imported}"
                    nodes.setdefault(
                        target, Node(id=target, kind="rust_module", label=imported)
                    )
                else:
                    target = f"external:{root_segment}"
                    nodes.setdefault(
                        target,
                        Node(
                            id=target,
                            kind="external_package",
                            label=root_segment,
                            module=root_segment,
                        ),
                    )

                edges.append(
                    Edge(
                        source=source,
                        target=target,
                        kind="imports",
                        raw=imported,
                        lineno=lineno,
                    )
                )

    return ScannerResult(nodes=list(nodes.values()), edges=edges, issues=issues)


SCANNERS: dict[str, ScannerFn] = {
    "python": scan_python,
    "javascript": scan_javascript,
    "go": scan_go,
    "rust": scan_rust,
}


def build_dependency_graph(
    project_root: Path, scanners: list[str] | None = None
) -> dict[str, Any]:
    project_root = project_root.resolve()
    scanner_names = scanners if scanners is not None else list(DEFAULT_SCANNERS)

    nodes: dict[str, Node] = {}
    edges: list[Edge] = []
    issues: list[dict[str, str]] = []

    for name in scanner_names:
        scanner = SCANNERS.get(name)
        if scanner is None:
            continue
        result = scanner(project_root)
        for node in result.nodes:
            nodes.setdefault(node.id, node)
        edges.extend(result.edges)
        issues.extend(result.issues)

    internal_nodes = [node for node in nodes.values() if node.kind.endswith("_module")]
    external_nodes = [
        node for node in nodes.values() if node.kind == "external_package"
    ]

    return {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "scanners": scanner_names,
        "nodes": [
            asdict(node) for node in sorted(nodes.values(), key=lambda item: item.id)
        ],
        "edges": [asdict(edge) for edge in edges],
        "issues": issues,
        "summary": {
            "internal_modules": len(internal_nodes),
            "external_packages": len(external_nodes),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "issues": len(issues),
        },
    }


def write_dependency_graph(graph: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build_and_persist_dependency_graph(
    project_root: Path, output_path: Path
) -> dict[str, Any]:
    graph = build_dependency_graph(project_root)
    write_dependency_graph(graph, output_path)
    return graph
