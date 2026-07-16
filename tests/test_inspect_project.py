from __future__ import annotations

import json
from pathlib import Path

from ai.tools.inspect_project import inspect_project


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_context_yaml(project_root: Path) -> None:
    _write(
        project_root / "ai" / "context.yaml",
        "ignore_dirs: []\nignore_top_level_files: []\n",
    )


def test_detects_go_language_and_module(tmp_path: Path) -> None:
    _write_context_yaml(tmp_path)
    _write(tmp_path / "go.mod", "module example.com/demo\n\ngo 1.22\n")
    _write(tmp_path / "main.go", 'package main\n\nfunc main() {}\n')

    result = inspect_project(tmp_path)

    assert "go" in result["project"]["languages"]
    assert "service" in result["project"]["project_types"]
    assert result["go_stack"]["module"] == "example.com/demo"


def test_detects_rust_language_and_crate(tmp_path: Path) -> None:
    _write_context_yaml(tmp_path)
    _write(
        tmp_path / "Cargo.toml",
        '[package]\nname = "demo"\nversion = "0.1.0"\n',
    )
    _write(tmp_path / "src" / "main.rs", "fn main() {}\n")

    result = inspect_project(tmp_path)

    assert "rust" in result["project"]["languages"]
    assert "service" in result["project"]["project_types"]
    assert result["rust_stack"]["crates"] == ["demo"]


def test_detects_react_and_nextjs_frameworks(tmp_path: Path) -> None:
    _write_context_yaml(tmp_path)
    _write(
        tmp_path / "package.json",
        json.dumps(
            {
                "name": "demo",
                "dependencies": {"react": "^18.0.0", "next": "^14.0.0"},
                "devDependencies": {"vite": "^5.0.0"},
            }
        ),
    )
    _write(tmp_path / "app" / "page.tsx", "export default function Page() { return null; }\n")

    result = inspect_project(tmp_path)

    assert "javascript" in result["project"]["languages"]
    assert "frontend" in result["project"]["project_types"]
    assert result["js_stack"]["frameworks"] == ["nextjs", "react"]
    assert result["js_stack"]["build_tools"] == ["vite"]


def test_detects_aws_sdk_js_as_cloud_provider(tmp_path: Path) -> None:
    _write_context_yaml(tmp_path)
    _write(
        tmp_path / "package.json",
        json.dumps({"name": "demo", "dependencies": {"@aws-sdk/client-s3": "^3.0.0"}}),
    )

    result = inspect_project(tmp_path)

    assert "aws" in result["cloud"]["providers"]


def test_no_js_go_rust_files_yields_empty_stacks(tmp_path: Path) -> None:
    _write_context_yaml(tmp_path)
    _write(tmp_path / "main.py", "import os\n")

    result = inspect_project(tmp_path)

    assert result["js_stack"] == {"frameworks": [], "build_tools": []}
    assert result["go_stack"] == {"module": None}
    assert result["rust_stack"] == {"crates": []}
