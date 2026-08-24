#!/usr/bin/env python3
"""Run Axiom's standard-library publication policy suite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.aggregate import main as aggregate_main  # noqa: E402
from axiom_validation.routing_evals import (  # noqa: E402
    validate_external_routing_observation,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--post-tag-routing-observation",
        type=Path,
        help="validate one content-addressed routing observation outside the repository",
    )
    parser.add_argument("--expected-version")
    parser.add_argument("--expected-tag")
    parser.add_argument("--expected-commit")
    parser.add_argument("--expected-tree")
    args = parser.parse_args(argv)
    binding_values = (
        args.expected_version,
        args.expected_tag,
        args.expected_commit,
        args.expected_tree,
    )
    if args.post_tag_routing_observation is None:
        if any(value is not None for value in binding_values):
            parser.error(
                "expected release bindings require --post-tag-routing-observation"
            )
    elif any(value is None for value in binding_values):
        parser.error(
            "--post-tag-routing-observation requires expected version, tag, commit, and tree"
        )
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.post_tag_routing_observation is None:
        return aggregate_main()

    path = args.post_tag_routing_observation
    if not path.is_absolute():
        path = Path.cwd() / path
    failures: list[str] = []
    digest = validate_external_routing_observation(
        path,
        expected_version=args.expected_version,
        expected_tag=args.expected_tag,
        expected_commit=args.expected_commit,
        expected_tree=args.expected_tree,
        failures=failures,
    )
    if failures:
        print("Post-tag routing observation validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "Post-tag routing observation validation passed: "
        f"{args.expected_tag} at {args.expected_commit}, tree {args.expected_tree}, "
        f"sha256 {digest}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
