"""Deterministic README facts rendered from the packaged skill metadata."""

from __future__ import annotations

from pathlib import Path

from .context import REPOSITORY_ROOT
from .repository_policy import SKILL_REFERENCE_ORDER
from .yaml_subset import CanonicalYamlError, parse_agent_metadata_document

README_RELATIVE = "README.md"
SKILL_REFERENCE_RELATIVE = "docs/reference/skills.md"
README_BADGES_START = "<!-- readme:badges:start -->"
README_BADGES_END = "<!-- readme:badges:end -->"
README_SKILL_INDEX_START = "<!-- readme:skill-index:start -->"
README_SKILL_INDEX_END = "<!-- readme:skill-index:end -->"
RELEASE_BADGE = (
    "[![Latest release](https://img.shields.io/github/v/release/wheakerd/axiom"
    "?sort=semver&style=for-the-badge&label=release&color=0f766e)]"
    "(https://github.com/wheakerd/axiom/releases/latest)"
)
HOSTS_BADGE = (
    "[![Hosts: Codex and Claude Code](https://img.shields.io/badge/hosts-"
    "Codex%20%7C%20Claude%20Code-6d28d9?style=for-the-badge)](docs/compatibility.md)"
)
LICENSE_BADGE = (
    "[![License: MIT](https://img.shields.io/badge/license-MIT-b45309"
    "?style=for-the-badge)](LICENSE)"
)


def load_skill_summaries(
    failures: list[str], *, root: Path = REPOSITORY_ROOT
) -> tuple[tuple[str, str], ...] | None:
    """Read each bundled skill's short description in Skill Reference order."""
    summaries: list[tuple[str, str]] = []
    for name in SKILL_REFERENCE_ORDER:
        relative = f"plugin/skills/{name}/agents/openai.yaml"
        try:
            text = (root / relative).read_text(encoding="utf-8")
            interface = parse_agent_metadata_document(text, relative)["interface"]
        except (OSError, UnicodeError) as error:
            failures.append(f"cannot read {relative}: {error}")
            continue
        except CanonicalYamlError as error:
            failures.append(str(error))
            continue
        summary = interface["short_description"]
        if not summary or not summary.isascii() or "|" in summary or "`" in summary:
            failures.append(
                f"{relative} short_description must be non-empty ASCII without "
                "table or code delimiters"
            )
            continue
        summaries.append((name, summary))
    if len(summaries) != len(SKILL_REFERENCE_ORDER):
        return None
    return tuple(summaries)


def render_badges(summaries: tuple[tuple[str, str], ...]) -> str:
    """Render the identity badge row on one line, counting the bundled skills."""
    count = len(summaries)
    skills_badge = (
        f"[![Skills: {count}](https://img.shields.io/badge/skills-{count}-0369a1"
        f"?style=for-the-badge)]({SKILL_REFERENCE_RELATIVE})"
    )
    return " ".join((RELEASE_BADGE, skills_badge, HOSTS_BADGE, LICENSE_BADGE))


def render_skill_index(summaries: tuple[tuple[str, str], ...]) -> str:
    """Render one table row per bundled skill, linked to its reference entry."""
    rows = ["| Skill | What it does |", "| --- | --- |"]
    rows.extend(
        f"| [`{name}`]({SKILL_REFERENCE_RELATIVE}#{name}) | {summary} |"
        for name, summary in summaries
    )
    return "\n".join(rows)


def _replace_block(text: str, start_marker: str, end_marker: str, body: str) -> str:
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise ValueError(f"{start_marker} and {end_marker} must each appear exactly once")
    start = text.index(start_marker) + len(start_marker)
    end = text.find(end_marker, start)
    if end < 0:
        raise ValueError(f"{end_marker} must follow {start_marker}")
    return text[:start] + "\n" + body + "\n" + text[end:]


def replace_readme_blocks(text: str, summaries: tuple[tuple[str, str], ...]) -> str:
    """Replace both managed README regions with their current rendering."""
    text = _replace_block(
        text, README_BADGES_START, README_BADGES_END, render_badges(summaries)
    )
    return _replace_block(
        text,
        README_SKILL_INDEX_START,
        README_SKILL_INDEX_END,
        render_skill_index(summaries),
    )


def check_readme_facts(failures: list[str], *, root: Path = REPOSITORY_ROOT) -> int:
    """Require the README badge row and skill index to match the skill metadata."""
    summaries = load_skill_summaries(failures, root=root)
    if summaries is None:
        return 0
    try:
        text = (root / README_RELATIVE).read_text(encoding="utf-8")
        expected = replace_readme_blocks(text, summaries)
    except (OSError, UnicodeError, ValueError) as error:
        failures.append(f"cannot validate {README_RELATIVE} generated skill facts: {error}")
        return 0
    if text != expected:
        failures.append(
            f"{README_RELATIVE} generated skill facts are stale; run "
            "python3 scripts/render-release-facts.py --render"
        )
    return len(summaries)


__all__ = (
    "README_BADGES_END",
    "README_BADGES_START",
    "README_RELATIVE",
    "README_SKILL_INDEX_END",
    "README_SKILL_INDEX_START",
    "check_readme_facts",
    "load_skill_summaries",
    "render_badges",
    "render_skill_index",
    "replace_readme_blocks",
)
