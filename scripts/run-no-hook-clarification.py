#!/usr/bin/env python3
"""Prepare/check/run the separately authorized single-reply clarification supplement."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from axiom_validation.no_hook_clarification import main
if __name__ == "__main__":
    raise SystemExit(main())
