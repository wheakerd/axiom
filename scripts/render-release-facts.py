#!/usr/bin/env python3
"""Check or explicitly render canonical release facts and route boundaries."""

from __future__ import annotations

import argparse
import stat
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.release_facts import (  # noqa: E402
    FACTS_SURFACES,
    FACTS_SURFACE_VERSIONS,
    check_release_facts,
    load_release_facts,
    replace_release_block,
)
from axiom_validation.route_catalog import (  # noqa: E402
    ROUTE_SURFACES,
    check_route_catalog,
    load_route_catalog,
    replace_route_block,
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
    release_documents = {
        version: document
        for version in sorted(set(FACTS_SURFACE_VERSIONS.values()))
        if (document := load_release_facts(version, failures)) is not None
    }
    route_document = load_route_catalog(failures)
    if (
        len(release_documents) != len(set(FACTS_SURFACE_VERSIONS.values()))
        or route_document is None
    ):
        return 0, failures

    rendered: dict[Path, str] = {}
    for relative_path in sorted(set((*FACTS_SURFACES, *ROUTE_SURFACES))):
        path = REPOSITORY_ROOT / relative_path
        try:
            text = _load_regular_text(path)
            if relative_path in FACTS_SURFACES:
                release_document = release_documents[
                    FACTS_SURFACE_VERSIONS[relative_path]
                ]
                text = replace_release_block(relative_path, text, release_document)
            if relative_path in ROUTE_SURFACES:
                text = replace_route_block(text, route_document)
        except (OSError, UnicodeError, ValueError) as error:
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


def _check() -> tuple[int, int, list[str]]:
    failures: list[str] = []
    fact_surfaces = check_release_facts(failures)
    route_scenarios = check_route_catalog(failures)
    return fact_surfaces, route_scenarios, failures


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

    fact_surfaces, route_scenarios, failures = _check()
    if failures:
        print("Canonical fact validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    action = f"rendered {changed} changed files and " if arguments.render else ""
    print(
        "Canonical fact validation passed: "
        f"{action}{fact_surfaces} release-fact surfaces and "
        f"{route_scenarios} structured route scenarios; static counts remain "
        "proxies, token figures remain estimates, and host observation is not inferred."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
