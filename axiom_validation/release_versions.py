"""Canonical production-release version grammar and regression corpus."""

from __future__ import annotations

import re


# Formal upstream releases are stable numeric versions only. Prerelease or
# build-metadata support requires a separately reviewed publication design.
PRODUCTION_RELEASE_NUMBER_PATTERN = r"0|[1-9][0-9]*"
PRODUCTION_RELEASE_VERSION_PATTERN = (
    rf"(?:{PRODUCTION_RELEASE_NUMBER_PATTERN})\."
    rf"(?:{PRODUCTION_RELEASE_NUMBER_PATTERN})\."
    rf"(?:{PRODUCTION_RELEASE_NUMBER_PATTERN})"
)
PRODUCTION_RELEASE_VERSION = re.compile(PRODUCTION_RELEASE_VERSION_PATTERN)
PRODUCTION_RELEASE_TAG_ERE_PATTERN = (
    rf"^v({PRODUCTION_RELEASE_NUMBER_PATTERN})\."
    rf"({PRODUCTION_RELEASE_NUMBER_PATTERN})\."
    rf"({PRODUCTION_RELEASE_NUMBER_PATTERN})$"
)

# The JavaScript signed-target guard, Bash publication gate, manifests, release
# evidence, and attestation subjects are all checked against this same corpus.
PRODUCTION_RELEASE_VERSION_CASES: tuple[tuple[str, str, bool], ...] = (
    ("zero-major", "0.8.18", True),
    ("one-zero-zero", "1.0.0", True),
    ("multi-digit", "12.34.56", True),
    ("arbitrary-precision", f"{'9' * 5000}.0.0", True),
    ("prerelease", "1.0.0-rc.1", False),
    ("build-metadata", "1.0.0+build.7", False),
    ("prerelease-build", "1.0.0-rc.1+build.7", False),
    ("leading-zero-major", "01.0.0", False),
    ("leading-zero-minor", "1.00.0", False),
    ("manifest-tag-prefix", "v1.0.0", False),
    ("missing-patch", "1.0", False),
    ("extra-component", "1.0.0.0", False),
)


ProductionReleaseComponent = tuple[int, str]
ProductionReleasePrecedence = tuple[
    ProductionReleaseComponent,
    ProductionReleaseComponent,
    ProductionReleaseComponent,
]


def parse_production_release_version(value: object) -> ProductionReleasePrecedence | None:
    """Return numeric precedence for one stable production version."""
    if not isinstance(value, str) or PRODUCTION_RELEASE_VERSION.fullmatch(value) is None:
        return None
    major, minor, patch = value.split(".")
    return (
        (len(major), major),
        (len(minor), minor),
        (len(patch), patch),
    )


def parse_production_release_tag(value: object) -> ProductionReleasePrecedence | None:
    """Return numeric precedence for one exact ``v<production-version>`` tag."""
    if not isinstance(value, str) or not value.startswith("v"):
        return None
    return parse_production_release_version(value[1:])
