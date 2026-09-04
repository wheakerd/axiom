#!/usr/bin/env python3
"""Validate the Codex no-Hook protocol; execution needs a separate gate."""

from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.no_hook_observation import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
