from __future__ import annotations

from pathlib import Path

from ai.runtime.dependency_graph import (
    DEFAULT_SCANNERS,
    build_dependency_graph,
    scan_go,
    scan_javascript,
    scan_python,
    scan_rust,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_python_builds_internal_and_external_nodes(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "__init__.py", "")
    _write(tmp_path / "src" / "main.py", "import json\nfrom src.helpers import util\n")
    _write(tmp_path / "src" / "helpers.py", "import requests\n")
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    result = scan_python(tmp_path)

    node_ids = {node.id for node in result.nodes}
    assert "module:src.main" in node_ids
    assert "module:src.helpers" in node_ids
    assert "external:json" in node_ids
    assert "external:requests" in node_ids

    edge_targets = {(edge.source, edge.target) for edge in result.edges}
    assert ("module:src.main", "module:src.helpers") in edge_targets
    assert ("module:src.main", "external:json") in edge_targets


def test_scan_javascript_resolves_relative_and_external_imports(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "App.tsx",
        "import React from 'react';\nimport { helper } from './helpers';\n",
    )
    _write(tmp_path / "src" / "helpers.ts", "export const helper = () => 1;\n")
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    result = scan_javascript(tmp_path)

    node_ids = {node.id for node in result.nodes}
    assert "module:src/App" in node_ids
    assert "module:src/helpers" in node_ids
    assert "external:react" in node_ids

    edge_targets = {(edge.source, edge.target) for edge in result.edges}
    assert ("module:src/App", "module:src/helpers") in edge_targets
    assert ("module:src/App", "external:react") in edge_targets


def test_scan_go_builds_internal_and_external_nodes(tmp_path: Path) -> None:
    _write(tmp_path / "go.mod", "module example.com/demo\n\ngo 1.22\n")
    _write(
        tmp_path / "main.go",
        'package main\n\nimport (\n\t"fmt"\n\n\t"example.com/demo/internal/greet"\n)\n\n'
        'func main() {\n\tfmt.Println(greet.Hello())\n}\n',
    )
    _write(
        tmp_path / "internal" / "greet" / "greet.go",
        'package greet\n\nimport "strings"\n\nfunc Hello() string {\n\treturn strings.ToUpper("hi")\n}\n',
    )
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    result = scan_go(tmp_path)

    node_ids = {node.id for node in result.nodes}
    assert "module:." in node_ids
    assert "module:internal/greet" in node_ids
    assert "external:fmt" in node_ids
    assert "external:strings" in node_ids

    edge_targets = {(edge.source, edge.target) for edge in result.edges}
    assert ("module:.", "module:internal/greet") in edge_targets
    assert ("module:.", "external:fmt") in edge_targets
    assert ("module:internal/greet", "external:strings") in edge_targets


def test_scan_rust_resolves_crate_and_external_imports(tmp_path: Path) -> None:
    _write(
        tmp_path / "src" / "main.rs",
        "mod helpers;\n\nuse crate::helpers::greet;\nuse serde::Serialize;\n\n"
        "fn main() {\n    greet();\n}\n",
    )
    _write(
        tmp_path / "src" / "helpers.rs",
        "pub fn greet() {\n    println!(\"hi\");\n}\n",
    )
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    result = scan_rust(tmp_path)

    node_ids = {node.id for node in result.nodes}
    assert "module:crate" in node_ids
    assert "module:helpers" in node_ids
    assert "external:serde" in node_ids

    edge_targets = {(edge.source, edge.target) for edge in result.edges}
    assert ("module:crate", "module:helpers") in edge_targets
    assert ("module:crate", "external:serde") in edge_targets


def test_build_dependency_graph_with_explicit_scanners(tmp_path: Path) -> None:
    _write(tmp_path / "main.py", "import os\n")
    _write(tmp_path / "src" / "App.tsx", "import React from 'react';\n")
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    graph = build_dependency_graph(tmp_path, scanners=["python", "javascript"])

    assert graph["scanners"] == ["python", "javascript"]
    node_ids = {node["id"] for node in graph["nodes"]}
    assert "module:main" in node_ids
    assert "module:src/App" in node_ids
    assert "external:os" in node_ids
    assert "external:react" in node_ids


def test_build_dependency_graph_defaults_to_all_language_scanners(tmp_path: Path) -> None:
    _write(tmp_path / "main.py", "import os\n")
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    graph = build_dependency_graph(tmp_path)

    assert graph["scanners"] == list(DEFAULT_SCANNERS)
    assert set(DEFAULT_SCANNERS) == {"python", "javascript", "go", "rust"}


def test_build_dependency_graph_covers_go_and_rust_by_default(tmp_path: Path) -> None:
    _write(tmp_path / "go.mod", "module example.com/demo\n\ngo 1.22\n")
    _write(tmp_path / "main.go", 'package main\n\nimport "fmt"\n\nfunc main() {}\n')
    _write(tmp_path / "src" / "main.rs", "fn main() {}\n")
    _write(
        tmp_path / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )

    graph = build_dependency_graph(tmp_path)

    node_ids = {node["id"] for node in graph["nodes"]}
    assert "module:." in node_ids
    assert "module:crate" in node_ids
