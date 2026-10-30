"""Readability contract for the bundled skill text: named invariants, bounded sentences, no blanket binding clause."""

from __future__ import annotations

import re
from pathlib import Path

from .context import REPOSITORY_ROOT, display_path

BUNDLED_SKILLS_ROOT = REPOSITORY_ROOT / "plugin" / "skills"
SENTENCE_MAX_CHARS = 300
INVARIANT_MIN = 3
INVARIANT_MAX = 6
INVARIANTS_HEADING = "## Invariants"
# A clause that binds everything a skill did not list as a default. Each skill
# names its invariants instead; every other statement is an adaptable default.
BLANKET_BINDING_CLAUSE = re.compile(r"\bevery other (?:rule|statement|instruction)s?\b", re.IGNORECASE)
LIST_ITEM = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
TERMINATOR_SPLIT = re.compile(r"(?<=[.!?])\s+")
NUMBERED_ITEM = re.compile(r"^(\d+)\.\s+\S")


def bundled_skill_files(root: Path = BUNDLED_SKILLS_ROOT) -> list[Path]:
    """Return every Markdown file of the bundled skills, sorted."""
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def text_units(text: str) -> list[str]:
    """Split Markdown into prose units: one per paragraph, list item, heading, or frontmatter field.

    Hard-wrapped continuation lines join their unit. Fenced code blocks and table
    rows are not prose and are skipped.
    """
    units: list[str] = []
    current: list[str] = []
    in_fence = False

    def flush() -> None:
        if current:
            units.append(" ".join(part.strip() for part in current))
            current.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped or stripped == "---" or stripped.startswith("|") or stripped.startswith("<!--"):
            flush()
            continue
        if stripped.startswith("#") or LIST_ITEM.match(stripped) or re.match(r"^[a-z][a-z-]*:\s", stripped):
            flush()
            current.append(LIST_ITEM.sub("", stripped).lstrip("#").strip())
            continue
        current.append(stripped)
    flush()
    return units


def sentences(unit: str) -> list[str]:
    """Split one prose unit at a terminator followed by whitespace; never longer than the true sentence."""
    return [part.strip() for part in TERMINATOR_SPLIT.split(unit) if part.strip()]


def long_sentences(text: str, limit: int = SENTENCE_MAX_CHARS) -> list[str]:
    """Return every sentence longer than the limit."""
    found = []
    for unit in text_units(text):
        for sentence in sentences(unit):
            if len(sentence) > limit:
                found.append(sentence)
    return found


def invariant_items(text: str) -> list[str] | None:
    """Return the numbered items of the Invariants section, or None when the section is absent."""
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == INVARIANTS_HEADING)
    except StopIteration:
        return None
    items: list[str] = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        match = NUMBERED_ITEM.match(line.strip())
        if match:
            items.append(line.strip())
    return items


def check_skill_text(failures: list[str], root: Path = BUNDLED_SKILLS_ROOT) -> int:
    """Validate the readability contract; return the number of skill entry files checked."""
    entries = 0
    for path in bundled_skill_files(root):
        label = display_path(path) if root == BUNDLED_SKILLS_ROOT else path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        for sentence in long_sentences(text):
            failures.append(
                f"{label} has a sentence of {len(sentence)} characters; the maximum is "
                f"{SENTENCE_MAX_CHARS}: {sentence[:80]!r}..."
            )
        if path.name != "SKILL.md" or path.parent.parent != root:
            continue
        entries += 1
        items = invariant_items(text)
        if items is None:
            failures.append(f"{label} lacks an `{INVARIANTS_HEADING}` section")
        elif not INVARIANT_MIN <= len(items) <= INVARIANT_MAX:
            failures.append(
                f"{label} lists {len(items)} invariants; the section needs {INVARIANT_MIN} to {INVARIANT_MAX}"
            )
        else:
            numbers = [int(NUMBERED_ITEM.match(item).group(1)) for item in items]
            if numbers != list(range(1, len(items) + 1)):
                failures.append(f"{label} numbers its invariants {numbers}; they must run from 1")
        for unit in text_units(text):
            for sentence in sentences(unit):
                if BLANKET_BINDING_CLAUSE.search(sentence):
                    failures.append(
                        f"{label} keeps a blanket binding clause instead of named invariants: {sentence[:80]!r}..."
                    )
    return entries
