"""Shared disposable input tree for the frozen no-Hook regression suites.

The test process owns this tree until exit, including imports between suites.
Current package validation continues to use axiom_validation.context instead.
"""

import atexit

from axiom_validation.historical_no_hook import historical_snapshot

_snapshot = historical_snapshot()
ROOT = _snapshot.__enter__()
atexit.register(_snapshot.__exit__, None, None, None)
