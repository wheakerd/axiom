#!/usr/bin/env python3
"""Build one deterministic Axiom Hook-independent compatibility bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.no_hook_bundle import (  # noqa: E402
    BundleContractError,
    build_bundle,
)


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument(
        "--git-executable",
        type=Path,
        required=True,
        help="absolute path to the Git executable frozen for every object read",
    )
    argument_parser.add_argument(
        "--source-repository",
        type=Path,
        required=True,
        help="exact local Git worktree that owns the source object database",
    )
    argument_parser.add_argument(
        "--source-commit",
        required=True,
        help="full lowercase commit OID used as the immutable source",
    )
    argument_parser.add_argument(
        "--expected-source-tree",
        required=True,
        help="full lowercase tree OID required for --source-commit",
    )
    argument_parser.add_argument(
        "--destination",
        type=Path,
        required=True,
        help="existing empty external directory exclusively owned by the caller",
    )
    return argument_parser


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        result = build_bundle(
            arguments.source_repository,
            arguments.source_commit,
            arguments.expected_source_tree,
            arguments.destination,
            git_executable=arguments.git_executable,
        )
    except BundleContractError as error:
        print(f"Hook-independent bundle build failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result.summary(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
