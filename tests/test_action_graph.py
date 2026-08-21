"""Focused tests for GitHub Actions graph policy."""

import unittest

from axiom_validation.action_graph import check_distribution_workflow_contract, check_github_action_pins
from tests.fixtures.action_graph import check_action_graph_fixtures


class ActionGraphTests(unittest.TestCase):
    def test_checked_in_action_graph(self):
        failures = []
        count = check_github_action_pins(failures)
        document = check_distribution_workflow_contract(failures)
        self.assertEqual(2, count)
        self.assertIsNotNone(document)
        self.assertEqual([], failures)

    def test_action_graph_mutations_are_rejected(self):
        failures = []
        count = check_action_graph_fixtures(failures)
        self.assertEqual(7, count)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
