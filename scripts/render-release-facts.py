#!/usr/bin/env python3
"""Check or explicitly render the managed route-boundary, runtime-identity, and README blocks."""

from __future__ import annotations

import argparse
import stat
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.readme_facts import (  # noqa: E402
    check_readme_facts,
    load_skill_summaries,
    readme_surfaces,
    replace_readme_blocks,
)
from axiom_validation.route_catalog import (  # noqa: E402
    ROUTE_SURFACES,
    check_route_catalog,
    load_route_catalog,
    replace_route_block,
)
from axiom_validation.runtime_identity import (  # noqa: E402
    IDENTITY_RELATIVE,
    POLICY_LEDGER_SURFACES,
    POLICY_REVISIONS_RELATIVE,
    RUNTIME_IDENTITY_SURFACES,
    check_runtime_identity,
    load_json_document,
    replace_policy_ledger_block,
    replace_runtime_identity_block,
)


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    modes = argument_parser.add_mutually_exclusive_group(required=True)
    modes.add_argument(
        "--check",
        action="store_true",
        help="verify canonical data and every managed surface without writing",
    )
    modes.add_argument(
        "--render",
        action="store_true",
        help="explicitly rewrite only the managed marker regions, then verify them",
    )
    return argument_parser


def _load_regular_text(path: Path) -> str:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"managed surface must be a regular non-symbolic-link file: {path}")
    return path.read_text(encoding="utf-8")


def _render() -> tuple[int, list[str]]:
    failures: list[str] = []
    route_document = load_route_catalog(failures)
    identity_document = load_json_document(
        REPOSITORY_ROOT / IDENTITY_RELATIVE,
        failures,
    )
    ledger_document = load_json_document(
        REPOSITORY_ROOT / POLICY_REVISIONS_RELATIVE,
        failures,
    )
    skill_summaries = load_skill_summaries(failures)
    if (
        route_document is None
        or identity_document is None
        or ledger_document is None
        or skill_summaries is None
    ):
        return 0, failures

    readme_paths = readme_surfaces(REPOSITORY_ROOT)
    rendered: dict[Path, str] = {}
    for relative_path in sorted(
        set(
            (
                *ROUTE_SURFACES,
                *RUNTIME_IDENTITY_SURFACES,
                *POLICY_LEDGER_SURFACES,
                *readme_paths,
            )
        )
    ):
        path = REPOSITORY_ROOT / relative_path
        try:
            text = _load_regular_text(path)
            if relative_path in ROUTE_SURFACES:
                text = replace_route_block(text, route_document)
            if relative_path in RUNTIME_IDENTITY_SURFACES:
                text = replace_runtime_identity_block(text, identity_document)
            if relative_path in POLICY_LEDGER_SURFACES:
                text = replace_policy_ledger_block(text, ledger_document)
            if relative_path in readme_paths:
                text = replace_readme_blocks(text, skill_summaries)
        except (KeyError, OSError, TypeError, UnicodeError, ValueError) as error:
            failures.append(f"cannot render {relative_path}: {error}")
            continue
        rendered[path] = text

    if failures:
        return 0, failures

    changed = 0
    for path, text in rendered.items():
        current = path.read_text(encoding="utf-8")
        if text == current:
            continue
        path.write_text(text, encoding="utf-8")
        changed += 1
    return changed, failures


def _check() -> tuple[int, int, int, list[str]]:
    failures: list[str] = []
    route_scenarios = check_route_catalog(failures)
    runtime_inputs = check_runtime_identity(failures)
    readme_skills = check_readme_facts(failures)
    return route_scenarios, runtime_inputs, readme_skills, failures


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    changed = 0
    if arguments.render:
        changed, render_failures = _render()
        if render_failures:
            print("Canonical fact rendering failed:", file=sys.stderr)
            for failure in render_failures:
                print(f"- {failure}", file=sys.stderr)
            return 1

    route_scenarios, runtime_inputs, readme_skills, failures = _check()
    if failures:
        print("Canonical fact validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    action = f"rendered {changed} changed files and " if arguments.render else ""
    print(
        "Canonical fact validation passed: "
        f"{action}{route_scenarios} structured route scenarios with "
        f"{runtime_inputs} canonical runtime inputs, plus a README index of "
        f"{readme_skills} bundled skills."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
