#!/usr/bin/env python3
"""Validate and bind exact GitHub Release evidence before publication."""

from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.release_evidence import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
