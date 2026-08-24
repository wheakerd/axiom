#!/usr/bin/env python3
"""Measure Axiom's routing gate with deterministic standard-library proxies."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.context_budget import (  # noqa: E402
    ROUTING_GATE_PATH,
    check_context_budget,
    measure_markdown,
)


def repository_path(raw_path: str) -> tuple[Path, str]:
    supplied = Path(raw_path)
    if supplied.is_absolute():
        raise ValueError("measurement path must be repository-relative")
    lexical = REPOSITORY_ROOT / supplied
    resolved = lexical.resolve()
    try:
        relative = resolved.relative_to(REPOSITORY_ROOT)
    except ValueError as error:
        raise ValueError("measurement path must remain inside the repository") from error
    return lexical, relative.as_posix()


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description=(
            "Report exact static counts used as routing-context proxies; "
            "no host usage is inferred."
        )
    )
    argument_parser.add_argument(
        "path",
        nargs="?",
        default=ROUTING_GATE_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        help="repository-relative UTF-8 Markdown path",
    )
    argument_parser.add_argument(
        "--check",
        action="store_true",
        help="validate the current versioned routing-context budget record",
    )
    return argument_parser


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.check:
        failures: list[str] = []
        scenario_count = check_context_budget(failures)
        if failures:
            print("Routing-context budget validation failed:", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1
        print(
            "Routing-context budget validation passed: "
            f"{scenario_count} lifecycle scenarios; scoped candidate F5 Codex usage is "
            "preserved without claiming v0.8.2 lifecycle evidence."
        )
        return 0

    try:
        path, relative_path = repository_path(arguments.path)
        metrics = measure_markdown(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Routing-context measurement failed: {error}", file=sys.stderr)
        return 1

    document = {
        "schemaVersion": "1",
        "path": relative_path,
        "sha256": digest,
        "measurementBoundary": {
            "staticCounts": "proxy",
            "estimatedTokens": "estimate",
            "exactHostUsage": "not-measured",
        },
        "metrics": metrics,
    }
    print(json.dumps(document, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
