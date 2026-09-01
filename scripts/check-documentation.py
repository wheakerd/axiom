#!/usr/bin/env python3
"""Validate Axiom's public documentation information architecture."""

from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.cases.documentation import (  # noqa: E402
    check_documentation_negative_fixtures,
)
from axiom_validation.documentation import check_documentation  # noqa: E402


def main() -> int:
    failures: list[str] = []
    report = check_documentation(failures)
    fixture_count = check_documentation_negative_fixtures(failures)
    if failures:
        print("Documentation validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "Documentation validation passed: "
        f"README {report.readme_bytes} bytes "
        f"(preferred 8-12 KiB: {report.preferred_budget_status}), "
        f"{report.markdown_count} Markdown files, "
        f"{report.current_document_count} current documents, "
        f"{report.indexed_document_count} indexed documents, "
        f"{report.generated_region_count} generated regions, "
        f"{fixture_count} negative fixtures."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
