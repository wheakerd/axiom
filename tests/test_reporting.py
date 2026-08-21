"""Focused tests for deterministic domain-local reporting."""

import unittest

from axiom_validation.reporting import run_policy


class ReportingTests(unittest.TestCase):
    def test_domain_is_attached_to_fixture_failure(self):
        failures = []

        def reject_fixture(local_failures):
            local_failures.append("fixture:tag-move expected rejection")
            return 1

        self.assertEqual(1, run_policy("release", reject_fixture, failures))
        self.assertEqual(
            ["[release] fixture:tag-move expected rejection"],
            failures,
        )


if __name__ == "__main__":
    unittest.main()
