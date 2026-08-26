"""Temporary Issue #56 pending and cancellation validation."""

import time
import unittest


class Issue56PendingCancellation(unittest.TestCase):
    def test_waits_for_cancellation(self):
        time.sleep(180)
        self.assertTrue(True)
