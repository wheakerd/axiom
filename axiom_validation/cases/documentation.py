"""Named negative fixtures for the documentation architecture validator."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.documentation import (
    check_docs_index_and_orphans,
    check_generated_marker_text,
    check_heading_text,
    check_hook_reference,
    check_lifecycle_text,
    check_private_guidance_text,
    check_readme_budget,
    check_readme_skill_inventory_text,
    check_task_navigation_text,
)
from axiom_validation.markdown import check_markdown_links


def _temporary_root() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory()
    return temporary, Path(temporary.name)


def _readme_oversize() -> list[str]:
    temporary, root = _temporary_root()
    try:
        (root / "README.md").write_text("# A\n" + "x" * (16 * 1024), encoding="utf-8")
        failures: list[str] = []
        check_readme_budget(root, failures)
        return failures
    finally:
        temporary.cleanup()


def _broken_relative_link() -> list[str]:
    temporary, root = _temporary_root()
    try:
        (root / "README.md").write_text(
            "# A\n\n[Missing](missing.md)\n", encoding="utf-8"
        )
        failures: list[str] = []
        check_markdown_links(failures, root=root)
        return failures
    finally:
        temporary.cleanup()


def _missing_local_anchor() -> list[str]:
    temporary, root = _temporary_root()
    try:
        (root / "README.md").write_text(
            "# A\n\n[Missing](target.md#absent)\n", encoding="utf-8"
        )
        (root / "target.md").write_text("# Present\n", encoding="utf-8")
        failures: list[str] = []
        check_markdown_links(failures, root=root)
        return failures
    finally:
        temporary.cleanup()


def _missing_h1() -> list[str]:
    failures: list[str] = []
    check_heading_text("docs/fixture.md", "## Fixture\n", failures)
    return failures


def _duplicate_h1() -> list[str]:
    failures: list[str] = []
    check_heading_text("docs/fixture.md", "# One\n\n# Two\n", failures)
    return failures


def _heading_skip() -> list[str]:
    failures: list[str] = []
    check_heading_text("docs/fixture.md", "# One\n\n### Three\n", failures)
    return failures


def _index_missing_current() -> list[str]:
    temporary, root = _temporary_root()
    try:
        docs = root / "docs"
        docs.mkdir()
        (docs / "README.md").write_text(
            "# Index\n\n## Start By Task\n\n[A](a.md)\n", encoding="utf-8"
        )
        (docs / "a.md").write_text("# A\n\n[B](b.md)\n", encoding="utf-8")
        (docs / "b.md").write_text("# B\n", encoding="utf-8")
        failures: list[str] = []
        check_docs_index_and_orphans(root, failures)
        return failures
    finally:
        temporary.cleanup()


def _current_orphan() -> list[str]:
    temporary, root = _temporary_root()
    try:
        docs = root / "docs"
        docs.mkdir()
        (docs / "README.md").write_text(
            "# Index\n\n## Start By Task\n\n[A](a.md)\n", encoding="utf-8"
        )
        (docs / "a.md").write_text("# A\n", encoding="utf-8")
        (docs / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
        failures: list[str] = []
        check_docs_index_and_orphans(root, failures)
        return failures
    finally:
        temporary.cleanup()


def _invalid_lifecycle() -> list[str]:
    failures: list[str] = []
    check_lifecycle_text(
        "docs/fixture.md", "# Fixture\n\n<!-- lifecycle: future -->\n", failures
    )
    return failures


def _lifecycle_path_mismatch() -> list[str]:
    failures: list[str] = []
    check_lifecycle_text(
        "docs/fixture.md",
        "# Fixture\n\n<!-- lifecycle: project-plan -->\n",
        failures,
    )
    return failures


def _unmatched_generated_marker() -> list[str]:
    failures: list[str] = []
    check_generated_marker_text(
        "docs/fixture.md", "<!-- facts:v1:start -->\nvalue\n", failures
    )
    return failures


def _nested_generated_marker() -> list[str]:
    failures: list[str] = []
    check_generated_marker_text(
        "docs/fixture.md",
        "<!-- outer:v1:start -->\n<!-- inner:v1:start -->\n"
        "<!-- inner:v1:end -->\n<!-- outer:v1:end -->\n",
        failures,
    )
    return failures


def _private_maintenance_link() -> list[str]:
    failures: list[str] = []
    check_private_guidance_text(
        "docs/fixture.md",
        "# Fixture\n\n[Private](https://github.com/wheakerd/axiom-maintainer)\n",
        failures,
    )
    return failures


def _historical_task_navigation() -> list[str]:
    failures: list[str] = []
    root = Path("/fixture").resolve()
    check_task_navigation_text(
        root / "docs" / "README.md",
        "# Index\n\n## Start By Task\n\n[Old](releases/v0.1.0.md)\n",
        root,
        failures,
    )
    return failures


def _project_task_navigation() -> list[str]:
    failures: list[str] = []
    root = Path("/fixture").resolve()
    check_task_navigation_text(
        root / "docs" / "README.md",
        "# Index\n\n## Start By Task\n\n[Plan](../project/README.md)\n",
        root,
        failures,
    )
    return failures


def _skill_inventory_drift() -> list[str]:
    failures: list[str] = []
    check_readme_skill_inventory_text(
        "# A\n\n### Shared skills\n\n- `using-axiom`, gate.\n",
        "# Gate\n\n## Bundled Routes\n\n- `fixture-route`: route.\n",
        failures,
    )
    return failures


def _hook_reference_drift() -> list[str]:
    temporary, root = _temporary_root()
    try:
        for relative_path in (
            "hooks/codex-hooks.json",
            "hooks/claude-hooks.json",
            "hooks/codex-session-start.cmd",
            "docs/reference/hooks.md",
        ):
            destination = root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPOSITORY_ROOT / relative_path, destination)
        reference = root / "docs" / "reference" / "hooks.md"
        reference.write_text(
            reference.read_text(encoding="utf-8")
            + "\n```bash\ncat \"${PLUGIN_ROOT}/skills/using-axiom/EXTRA.md\"\n```\n",
            encoding="utf-8",
        )
        failures: list[str] = []
        check_hook_reference(root, failures)
        return failures
    finally:
        temporary.cleanup()


NEGATIVE_FIXTURES: tuple[tuple[str, Callable[[], list[str]], str], ...] = (
    ("readme-oversize", _readme_oversize, "migration ceiling"),
    ("broken-relative-link", _broken_relative_link, "broken repository-relative link"),
    ("missing-local-anchor", _missing_local_anchor, "missing Markdown fragment"),
    ("missing-h1", _missing_h1, "exactly one H1"),
    ("duplicate-h1", _duplicate_h1, "exactly one H1"),
    ("heading-level-skip", _heading_skip, "skips a heading level"),
    ("index-missing-current", _index_missing_current, "does not directly index"),
    ("current-document-orphan", _current_orphan, "is orphaned"),
    ("invalid-lifecycle", _invalid_lifecycle, "invalid lifecycle value"),
    ("lifecycle-path-mismatch", _lifecycle_path_mismatch, "conflicts with its document class"),
    ("unmatched-generated-marker", _unmatched_generated_marker, "without an end"),
    ("nested-generated-marker", _nested_generated_marker, "nests generated marker"),
    ("private-maintenance-link", _private_maintenance_link, "private maintenance content"),
    ("historical-task-navigation", _historical_task_navigation, "historical or project-plan"),
    ("project-task-navigation", _project_task_navigation, "historical or project-plan"),
    ("skill-inventory-drift", _skill_inventory_drift, "differs from the canonical front door"),
    ("hook-reference-drift", _hook_reference_drift, "not present in the checked-in declarations"),
)


def check_documentation_negative_fixtures(failures: list[str]) -> int:
    """Prove each named documentation bypass is rejected deterministically."""
    rejected = 0
    for name, operation, expected in NEGATIVE_FIXTURES:
        observed = operation()
        if any(expected in failure for failure in observed):
            rejected += 1
        else:
            details = "; ".join(observed) if observed else "no failure"
            failures.append(
                f"documentation negative fixture {name!r} was accepted "
                f"(expected {expected!r}; observed {details})"
            )
    return rejected


__all__ = ("NEGATIVE_FIXTURES", "check_documentation_negative_fixtures")
