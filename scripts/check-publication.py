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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return argparse.ArgumentParser(description=__doc__).parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    parse_args(argv)
    return aggregate_main()


if __name__ == "__main__":
    raise SystemExit(main())
