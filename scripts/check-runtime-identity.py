#!/usr/bin/env python3
"""Check Axiom runtime identity or derive a digest from one package tree."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.runtime_identity import (  # noqa: E402
    INPUT_MANIFEST_RELATIVE,
    check_runtime_identity,
    compute_runtime_contract,
    load_json_document,
)


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    modes = argument_parser.add_mutually_exclusive_group(required=True)
    modes.add_argument(
        "--check",
        action="store_true",
        help="validate checked-in identity, history, policy revisions, and rendered facts",
    )
    modes.add_argument(
        "--digest-root",
        type=Path,
        help="derive a digest for this package root without writing it",
    )
    argument_parser.add_argument(
        "--manifest",
        type=Path,
        default=REPOSITORY_ROOT / INPUT_MANIFEST_RELATIVE,
        help="input manifest used with --digest-root (defaults to the checked-in v1 manifest)",
    )
    argument_parser.add_argument(
        "--historical",
        action="store_true",
        help="allow absent newly classified fields or excluded roots when deriving an old tag",
    )
    return argument_parser


def report_failures(failures: list[str]) -> int:
    print("Runtime identity validation failed:", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.check:
        if arguments.historical:
            parser().error("--historical requires --digest-root")
        failures: list[str] = []
        record_count = check_runtime_identity(failures)
        if failures:
            return report_failures(failures)
        print(
            "Runtime identity validation passed: "
            f"{record_count} canonical installed inputs, distinct plugin, policy, "
            "and runtime identities."
        )
        return 0

    root = arguments.digest_root.resolve()
    manifest_path = arguments.manifest.resolve()
    failures = []
    manifest = load_json_document(
        manifest_path,
        failures,
        root=manifest_path.parent,
    )
    contract = (
        compute_runtime_contract(
            root,
            manifest,
            failures,
            historical=arguments.historical,
        )
        if manifest is not None
        else None
    )
    if failures or contract is None:
        return report_failures(failures or ["runtime contract could not be computed"])
    print(
        json.dumps(
            {
                "schemaVersion": manifest["schemaVersion"],
                "runtimeContractDigest": contract.digest,
                "recordCount": contract.record_count,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
