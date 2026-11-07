"""Shared repository context and the release version a stamped tree carries."""

from __future__ import annotations

import os
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPOSITORY_ROOT / "README.md"
# `.ci/check.py --release-version X.Y.Z` sets this for its checks. Unset, the
# checks validate main, whose plugin manifests declare no version; set, they
# validate a release tree whose manifests CI stamped with that version.
RELEASE_VERSION_ENVIRONMENT = "AXIOM_RELEASE_VERSION"


def display_path(path: Path) -> str:
    """Render repository-owned paths without depending on the caller's cwd."""
    try:
        return path.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return str(path)


def expected_release_version() -> str | None:
    """Return the version a stamped release tree must declare, or None for main."""
    return os.environ.get(RELEASE_VERSION_ENVIRONMENT) or None


EXPECTED_RELEASE_VERSION = expected_release_version()
