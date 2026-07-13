from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_sample_project(project_root: Path) -> None:
    _write(
        project_root / "ai" / "context.yaml",
        """artifacts:
  - .ai/context_bundle.yaml
  - .ai/skills_registry.json
  - .ai/dependencies_graph.json
  - .ai/treemap.md

ignore_dirs:
  - .ai
  - __pycache__

treemap_ignore_dirs:
  - .ai
  - __pycache__

ignore_top_level_files: []

structure:
  python:
    - src/
    - scripts/

rules:
  - .ai/ is optional generated context and is never required at runtime.

entrypoint_roots:
  directories:
    - scripts
    - src/jobs

module_roots:
  directories:
    - src
""",
    )
    _write(
        project_root / "ai" / "skills.yaml",
        """example_skill:
  path: ai/skills/python/example.md
  description: Example skill
""",
    )
    _write(project_root / "ai" / "skills" / "python" / "example.md", "# Example\n")
    _write(project_root / "src" / "jobs" / "example_job.py", "import json\n")
    _write(project_root / "scripts" / "helper.py", "print('ok')\n")


def test_ai_refresh_wrapper_smoke(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/hooks/ai_refresh.py",
            "--project-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert '"mode": "full"' in result.stdout


def test_ruff_wrappers_smoke() -> None:
    check_result = subprocess.run(
        [
            sys.executable,
            "scripts/testing/run_ruff_check.py",
            "tests/test_example_job.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    format_result = subprocess.run(
        [
            sys.executable,
            "scripts/testing/run_ruff_format.py",
            "--check",
            "tests/test_example_job.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert check_result.returncode == 0, check_result.stderr
    assert format_result.returncode == 0, format_result.stderr


def test_pytest_wrapper_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/testing/run_pytest.py", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "pytest" in result.stdout.lower()


def test_pytest_wrapper_treats_no_tests_as_success(tmp_path: Path) -> None:
    _write(
        tmp_path / "requirements.txt",
        "",
    )

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/testing/run_pytest.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "No tests were collected" in result.stdout


def test_package_wrapper_builds_bundle_with_requirements(
    tmp_path: Path, monkeypatch
) -> None:
    import scripts.package as package

    fake_src = tmp_path / "src"
    fake_src.mkdir()
    (fake_src / "job.py").write_text("print('ok')\n", encoding="utf-8")
    fake_requirements = tmp_path / "requirements.txt"
    fake_requirements.write_text("pandas==2.0.0\n", encoding="utf-8")
    fake_artifact = tmp_path / "artifacts" / "bundle.zip"

    monkeypatch.setattr(package, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(package, "INCLUDE_DIRS", [fake_src])
    monkeypatch.setattr(package, "REQUIREMENTS_PATH", fake_requirements)
    monkeypatch.setattr(package, "ARTIFACT_PATH", fake_artifact)

    artifact = package.build_bundle()

    assert artifact == fake_artifact
    assert artifact.exists()

    from zipfile import ZipFile

    with ZipFile(artifact) as archive:
        names = set(archive.namelist())
    assert "src/job.py" in names
    assert "requirements.txt" in names
