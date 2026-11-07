#!/usr/bin/env python3
"""Run Axiom's repository checks the way CI runs them.

Usage:
  python3 -B .ci/check.py                 # publication aggregate, then the tests
  python3 -B .ci/check.py publication     # publication aggregate only
  python3 -B .ci/check.py tests [args]    # unit and integration tests (args go to unittest)
  python3 -B .ci/check.py hook-runtime [--report-environment]
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


CI_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = CI_ROOT.parent


def _run(*arguments: str) -> int:
    environment = {**os.environ, "PYTHONPATH": str(CI_ROOT)}
    return subprocess.run(
        [sys.executable, "-B", *arguments], cwd=REPOSITORY_ROOT, env=environment, check=False
    ).returncode


def publication() -> int:
    return _run(str(CI_ROOT / "scripts" / "check-publication.py"))


def tests(extra: list[str]) -> int:
    return _run(
        "-m", "unittest", "discover",
        "-s", str(CI_ROOT / "tests"), "-t", str(CI_ROOT), "-p", "test_*.py", *extra,
    )


def hook_runtime(extra: list[str]) -> int:
    if extra == ["--report-environment"]:
        return _run("-m", "tests.hook_runtime_integration", "--report-environment")
    return _run("-m", "unittest", "tests.hook_runtime_integration", "-v", *extra)


def main(argv: list[str]) -> int:
    command, extra = (argv[0], argv[1:]) if argv else ("all", [])
    if command == "publication" and not extra:
        return publication()
    if command == "tests":
        return tests(extra)
    if command == "hook-runtime":
        return hook_runtime(extra)
    if command == "all" and not extra:
        status = publication()
        return status if status else tests([])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
