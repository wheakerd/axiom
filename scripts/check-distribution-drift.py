#!/usr/bin/env python3
"""Fail when Axiom's distribution wrappers, docs, and skill tree drift."""

from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPOSITORY_ROOT / "skills"
README_PATH = REPOSITORY_ROOT / "README.md"
README_SKILLS_HEADING = "### Shared skills"
PLUGIN_NAME = "axiom"


class DriftGuardError(RuntimeError):
    """A distribution declaration could not be resolved safely."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise DriftGuardError(f"missing JSON file: {path.relative_to(REPOSITORY_ROOT)}") from error
    except json.JSONDecodeError as error:
        relative_path = path.relative_to(REPOSITORY_ROOT)
        raise DriftGuardError(
            f"invalid JSON in {relative_path}:{error.lineno}:{error.colno}: {error.msg}"
        ) from error

    if not isinstance(value, dict):
        raise DriftGuardError(f"expected a JSON object in {path.relative_to(REPOSITORY_ROOT)}")
    return value


def resolve_inside_repository(base: Path, raw_path: str, label: str) -> Path:
    candidate = (base / raw_path).resolve()
    try:
        candidate.relative_to(REPOSITORY_ROOT)
    except ValueError as error:
        raise DriftGuardError(f"{label} escapes the repository: {raw_path!r}") from error
    return candidate


def skill_names_on_disk() -> list[str]:
    if not SKILLS_ROOT.is_dir():
        raise DriftGuardError("missing skills/ directory")
    return sorted(
        child.name
        for child in SKILLS_ROOT.iterdir()
        if child.is_dir() and (child / "SKILL.md").is_file()
    )


def declared_skills(manifest_path: Path, plugin_root: Path, label: str) -> list[str]:
    manifest = load_json(manifest_path)
    declarations = manifest.get("skills")
    if declarations is None:
        return []
    if isinstance(declarations, str):
        paths = [declarations]
    elif isinstance(declarations, list) and all(isinstance(item, str) for item in declarations):
        paths = declarations
    else:
        raise DriftGuardError(f"{label} has a non-string skills declaration")

    names: list[str] = []
    for raw_path in paths:
        declared_path = resolve_inside_repository(plugin_root, raw_path, f"{label} skills path")
        if not declared_path.is_dir():
            raise DriftGuardError(f"{label} skills path is not a directory: {raw_path!r}")
        if (declared_path / "SKILL.md").is_file():
            names.append(declared_path.name)
            continue
        names.extend(
            child.name
            for child in declared_path.iterdir()
            if child.is_dir() and (child / "SKILL.md").is_file()
        )

    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise DriftGuardError(f"{label} declares duplicate skills: {', '.join(duplicates)}")
    return sorted(names)


def marketplace_plugin(data: dict[str, Any], label: str) -> dict[str, Any]:
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        raise DriftGuardError(f"{label} has no plugins array")
    matches = [entry for entry in plugins if isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME]
    if len(matches) != 1:
        raise DriftGuardError(f"{label} must contain exactly one {PLUGIN_NAME!r} plugin entry")
    return matches[0]


def codex_marketplace_skills() -> list[str]:
    label = ".agents/plugins/marketplace.json"
    entry = marketplace_plugin(load_json(REPOSITORY_ROOT / label), label)
    source = entry.get("source")
    if not isinstance(source, dict) or source.get("source") != "local":
        raise DriftGuardError(f"{label} must use a local source object")
    raw_path = source.get("path")
    if not isinstance(raw_path, str):
        raise DriftGuardError(f"{label} local source has no path")
    plugin_root = resolve_inside_repository(REPOSITORY_ROOT, raw_path, f"{label} source path")
    manifest = plugin_root / ".codex-plugin" / "plugin.json"
    return declared_skills(manifest, plugin_root, label)


def claude_marketplace_skills() -> list[str]:
    label = ".claude-plugin/marketplace.json"
    entry = marketplace_plugin(load_json(REPOSITORY_ROOT / label), label)
    raw_path = entry.get("source")
    if not isinstance(raw_path, str):
        raise DriftGuardError(f"{label} must use a relative string source")
    plugin_root = resolve_inside_repository(REPOSITORY_ROOT, raw_path, f"{label} source path")
    manifest = plugin_root / ".claude-plugin" / "plugin.json"
    return declared_skills(manifest, plugin_root, label)


def readme_skills() -> list[str]:
    lines = README_PATH.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(README_SKILLS_HEADING) + 1
    except ValueError as error:
        raise DriftGuardError(f"README.md is missing {README_SKILLS_HEADING!r}") from error

    names: list[str] = []
    skill_line = re.compile(r"^- `([a-z0-9]+(?:-[a-z0-9]+)*)`(?:[,: ]|$)")
    for line in lines[start:]:
        if line.startswith("##"):
            break
        match = skill_line.match(line)
        if match:
            names.append(match.group(1))

    if not names:
        raise DriftGuardError(f"README.md has no skill list below {README_SKILLS_HEADING!r}")
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise DriftGuardError(f"README.md lists duplicate skills: {', '.join(duplicates)}")
    return sorted(names)


def unified_skill_diff(label: str, declared: list[str], on_disk: list[str]) -> str:
    return "".join(
        difflib.unified_diff(
            [f"{name}\n" for name in declared],
            [f"{name}\n" for name in on_disk],
            fromfile=f"{label} (declared)",
            tofile="skills/ (on disk)",
        )
    )


def main() -> int:
    try:
        on_disk = skill_names_on_disk()
    except DriftGuardError as error:
        print(f"distribution drift guard error: {error}", file=sys.stderr)
        return 1

    checks: list[tuple[str, Callable[[], list[str]]]] = [
        (
            ".codex-plugin/plugin.json",
            lambda: declared_skills(
                REPOSITORY_ROOT / ".codex-plugin" / "plugin.json",
                REPOSITORY_ROOT,
                ".codex-plugin/plugin.json",
            ),
        ),
        (".agents/plugins/marketplace.json", codex_marketplace_skills),
        (
            ".claude-plugin/plugin.json",
            lambda: declared_skills(
                REPOSITORY_ROOT / ".claude-plugin" / "plugin.json",
                REPOSITORY_ROOT,
                ".claude-plugin/plugin.json",
            ),
        ),
        (".claude-plugin/marketplace.json", claude_marketplace_skills),
        ("README.md / What Gets Installed", readme_skills),
    ]

    failures: list[str] = []
    for label, collect in checks:
        try:
            declared = collect()
        except (DriftGuardError, OSError) as error:
            failures.append(f"{label}: {error}")
            continue
        if declared != on_disk:
            failures.append(unified_skill_diff(label, declared, on_disk))

    if failures:
        print("Distribution drift detected:\n", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(
        f"Distribution drift guard passed: {len(on_disk)} skills match both platform wrappers and README.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
