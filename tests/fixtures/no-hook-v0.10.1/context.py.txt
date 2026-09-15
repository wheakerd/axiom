"""Shared repository context and manifest-derived release identity."""

from __future__ import annotations

import json
from pathlib import Path

from .release_versions import parse_production_release_version


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPOSITORY_ROOT / "README.md"
MANIFEST_FILES = (
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
)
def display_path(path: Path) -> str:
    """Render repository-owned paths without depending on the caller's cwd."""
    try:
        return path.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return str(path)


def release_version(root: Path = REPOSITORY_ROOT) -> str | None:
    """Return the one stable production version shared by both manifests."""
    versions: list[str] = []
    for relative_path in MANIFEST_FILES:
        try:
            document = json.loads((root / relative_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        version = document.get("version") if isinstance(document, dict) else None
        if parse_production_release_version(version) is None:
            return None
        versions.append(version)
    return versions[0] if len(set(versions)) == 1 else None


RELEASE_VERSION = release_version() or "0.0.0"
CURRENT_RELEASE_NOTES = f"docs/releases/v{RELEASE_VERSION}.md"
