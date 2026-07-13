from __future__ import annotations

import json
from pathlib import Path

from scripts.restore_project import restore_project, validate_consistency


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_sample_project(project_root: Path) -> None:
    _write(
        project_root / "ai/context.yaml",
        """
artifacts:
  - .ai/context_bundle.yaml
  - .ai/skills_registry.json
  - .ai/dependencies_graph.json
  - .ai/treemap.md
ignore_dirs: [.ai, __pycache__]
treemap_ignore_dirs: [.ai, __pycache__]
ignore_top_level_files: []
structure: {}
rules: []
entrypoint_roots:
  directories: [src]
module_roots:
  directories: [src]
""",
    )
    _write(
        project_root / "ai/skills.yaml",
        """
python_skill:
  path: ai/skills/python/example.md
  description: Python guidance
saas_auth:
  path: ai/skills/saas/auth.md
  description: SaaS guidance
""",
    )
    _write(project_root / "ai/skills/python/example.md", "# Python\n")
    _write(project_root / "ai/skills/saas/auth.md", "# SaaS\n")
    _write(project_root / "src/main.py", "import json\n")


def test_validate_consistency_checks_all_declared_skill_files(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    assert validate_consistency(tmp_path) == {"missing": []}

    (tmp_path / "ai/skills/python/example.md").unlink()
    assert validate_consistency(tmp_path)["missing"] == ["ai/skills/python/example.md"]


def test_restore_dry_run_skips_dependency_install_and_context(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    payload = restore_project(tmp_path, dry_run=True)

    assert payload["dependencies"]["status"] == "skipped"
    assert payload["context"]["status"] == "skipped"


def test_restore_regenerates_context_artifacts_with_all_skills(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    payload = restore_project(tmp_path, dry_run=False)

    assert payload["context"]["status"] == "ok"
    registry = (tmp_path / ".ai/skills_registry.json").read_text(encoding="utf-8")
    assert "python_skill" in registry
    assert "saas_auth" in registry


def test_restore_skips_dependency_install_without_requirements_files(
    tmp_path: Path,
) -> None:
    _create_sample_project(tmp_path)

    payload = restore_project(tmp_path, dry_run=False)

    assert payload["dependencies"]["status"] == "skipped"
    assert payload["dependencies"]["reason"] == "no requirements files found"


def test_restore_is_idempotent(tmp_path: Path) -> None:
    _create_sample_project(tmp_path)

    first = restore_project(tmp_path, dry_run=False)

    def normalized(relative: str) -> str:
        content = (tmp_path / relative).read_text(encoding="utf-8")
        if relative.endswith("dependencies_graph.json"):
            payload = json.loads(content)
            payload.pop("generated_at", None)
            return json.dumps(payload, sort_keys=True)
        return content

    snapshot = {
        relative: normalized(relative) for relative in first["context"]["artifacts"]
    }
    second = restore_project(tmp_path, dry_run=False)

    assert second["context"]["artifacts"] == first["context"]["artifacts"]
    assert {
        relative: normalized(relative) for relative in second["context"]["artifacts"]
    } == snapshot
