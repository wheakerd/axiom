#!/usr/bin/env python3
"""Run the explicitly authorized native no-Hook observation protocol."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from axiom_validation.no_hook_native_observation import main


if __name__ == "__main__":
    raise SystemExit(main())
