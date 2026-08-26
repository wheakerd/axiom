"""Temporary Issue #56 merge-gate validation."""

import unittest


class Issue56DeliberateFailure(unittest.TestCase):
    def test_deliberate_failure(self):
        self.fail("Issue #56 validation fixture: deliberate failure")
