#!/usr/bin/env python3
"""Check or explicitly render the managed README blocks."""

from __future__ import annotations

import argparse
import stat
import sys
from pathlib import Path


CI_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CI_ROOT.parent
if str(CI_ROOT) not in sys.path:
    sys.path.insert(0, str(CI_ROOT))

from axiom_validation.readme_facts import (  # noqa: E402
    check_readme_facts,
    load_skill_summaries,
    readme_surfaces,
    replace_readme_blocks,
)


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    modes = argument_parser.add_mutually_exclusive_group(required=True)
    modes.add_argument(
        "--check",
        action="store_true",
        help="verify every managed surface without writing",
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
    skill_summaries = load_skill_summaries(failures)
    if skill_summaries is None:
        return 0, failures

    rendered: dict[Path, str] = {}
    for relative_path in sorted(readme_surfaces(REPOSITORY_ROOT)):
        path = REPOSITORY_ROOT / relative_path
        try:
            rendered[path] = replace_readme_blocks(_load_regular_text(path), skill_summaries)
        except (KeyError, OSError, TypeError, UnicodeError, ValueError) as error:
            failures.append(f"cannot render {relative_path}: {error}")

    if failures:
        return 0, failures

    changed = 0
    for path, text in rendered.items():
        if text == path.read_text(encoding="utf-8"):
            continue
        path.write_text(text, encoding="utf-8")
        changed += 1
    return changed, failures


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    changed = 0
    if arguments.render:
        changed, render_failures = _render()
        if render_failures:
            print("README fact rendering failed:", file=sys.stderr)
            for failure in render_failures:
                print(f"- {failure}", file=sys.stderr)
            return 1

    failures: list[str] = []
    readme_skills = check_readme_facts(failures)
    if failures:
        print("README fact validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    action = f"rendered {changed} changed files and " if arguments.render else ""
    print(
        "README fact validation passed: "
        f"{action}a README index of {readme_skills} bundled skills."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
