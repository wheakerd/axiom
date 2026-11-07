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
    check_markdown_language,
    check_private_guidance_text,
    check_skill_reference_inventory_text,
    check_translations,
)
from axiom_validation.markdown import check_markdown_links


def _temporary_root() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory()
    return temporary, Path(temporary.name)


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
            "# Index\n\n[A](a.md)\n", encoding="utf-8"
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
            "# Index\n\n[A](a.md)\n", encoding="utf-8"
        )
        (docs / "a.md").write_text("# A\n", encoding="utf-8")
        (docs / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
        failures: list[str] = []
        check_docs_index_and_orphans(root, failures)
        return failures
    finally:
        temporary.cleanup()


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


def _skill_inventory_drift() -> list[str]:
    failures: list[str] = []
    check_skill_reference_inventory_text(
        "# A\n\n## Shared skills\n\n### using-axiom\n",
        failures,
        inventory=("using-axiom", "fixture-route"),
    )
    return failures


def _hook_reference_drift() -> list[str]:
    temporary, root = _temporary_root()
    try:
        for relative_path in (
            "plugin/hooks/codex-hooks.json",
            "plugin/hooks/codex-session-start.cmd",
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


def _translation_pair(source: str, mirror: str) -> list[str]:
    temporary, root = _temporary_root()
    try:
        docs = root / "docs"
        docs.mkdir()
        if source is not None:
            (docs / "guide.md").write_text(source, encoding="utf-8")
        (docs / "guide.zh-CN.md").write_text(mirror, encoding="utf-8")
        failures: list[str] = []
        check_translations(root, failures)
        return failures
    finally:
        temporary.cleanup()


def _translation_missing_source() -> list[str]:
    return _translation_pair(None, "# Guide\n\n[English](guide.md)\n")


def _translation_heading_drift() -> list[str]:
    return _translation_pair(
        "# Guide\n\n[zh-CN](guide.zh-CN.md)\n\n## Install\n",
        "# Guide\n\n[English](guide.md)\n",
    )


def _translation_code_drift() -> list[str]:
    return _translation_pair(
        "# Guide\n\n[zh-CN](guide.zh-CN.md)\n\n```bash\ncodex plugin add axiom@axiom\n```\n",
        "# Guide\n\n[English](guide.md)\n\n```bash\ncodex plugin add axiom\n```\n",
    )


def _translation_generated_drift() -> list[str]:
    return _translation_pair(
        "# Guide\n\n[zh-CN](guide.zh-CN.md)\n\n<!-- facts:v1:start -->\nvalue\n<!-- facts:v1:end -->\n",
        "# Guide\n\n[English](guide.md)\n\n<!-- facts:v1:start -->\nother\n<!-- facts:v1:end -->\n",
    )


def _translation_link_drift() -> list[str]:
    return _translation_pair(
        "# Guide\n\n[zh-CN](guide.zh-CN.md)\n",
        "# Guide\n\n[English](guide.md) [Extra](README.md)\n",
    )


def _translation_missing_switcher() -> list[str]:
    return _translation_pair(
        "# Guide\n\n[zh-CN](guide.zh-CN.md)\n",
        "# Guide\n\nNo way back.\n",
    )


def _english_source_with_non_ascii() -> list[str]:
    temporary, root = _temporary_root()
    try:
        (root / "docs").mkdir()
        (root / "docs" / "guide.md").write_text("# Guide\n\nAxiom \u4e2d\u6587\n", encoding="utf-8")
        failures: list[str] = []
        check_markdown_language(root, failures)
        return failures
    finally:
        temporary.cleanup()


NEGATIVE_FIXTURES: tuple[tuple[str, Callable[[], list[str]], str], ...] = (
    ("broken-relative-link", _broken_relative_link, "broken repository-relative link"),
    ("missing-local-anchor", _missing_local_anchor, "missing Markdown fragment"),
    ("missing-h1", _missing_h1, "exactly one H1"),
    ("duplicate-h1", _duplicate_h1, "exactly one H1"),
    ("heading-level-skip", _heading_skip, "skips a heading level"),
    ("index-missing-current", _index_missing_current, "does not directly index"),
    ("current-document-orphan", _current_orphan, "is orphaned"),
    ("unmatched-generated-marker", _unmatched_generated_marker, "without an end"),
    ("nested-generated-marker", _nested_generated_marker, "nests generated marker"),
    ("private-maintenance-link", _private_maintenance_link, "private maintenance content"),
    ("skill-inventory-drift", _skill_inventory_drift, "differs from the canonical skill order"),
    ("hook-reference-drift", _hook_reference_drift, "not present in the checked-in declarations"),
    ("translation-missing-source", _translation_missing_source, "has no English source"),
    ("translation-heading-drift", _translation_heading_drift, "heading structure differs"),
    ("translation-code-drift", _translation_code_drift, "fenced code blocks differ"),
    ("translation-generated-drift", _translation_generated_drift, "generated regions differ"),
    ("translation-link-drift", _translation_link_drift, "link targets differ"),
    ("translation-missing-switcher", _translation_missing_switcher, "must link to its English source"),
    ("english-source-non-ascii", _english_source_with_non_ascii, "contains non-ASCII text"),
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
