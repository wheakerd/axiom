"""Focused tests for GitHub Actions graph policy."""

import unittest

from axiom_validation.action_graph import (
    check_distribution_workflow_contract,
    check_github_action_pins,
    check_unit_test_workflow_contract,
    check_unit_test_workflow_text,
)
from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.cases.action_graph import check_action_graph_fixtures


class ActionGraphTests(unittest.TestCase):
    def test_checked_in_action_graph(self):
        failures = []
        count = check_github_action_pins(failures)
        document = check_distribution_workflow_contract(failures)
        unit_test_document = check_unit_test_workflow_contract(failures)
        self.assertEqual(7, count)
        self.assertIsNotNone(document)
        self.assertIsNotNone(unit_test_document)
        self.assertEqual([], failures)

    def test_unit_test_workflow_security_and_toolchain_mutations_are_rejected(self):
        path = (
            REPOSITORY_ROOT
            / ".github"
            / "workflows"
            / "unit-and-integration-tests.yml"
        )
        original = path.read_text(encoding="utf-8")
        scenarios = (
            (
                "write permission",
                original.replace("contents: read", "contents: write", 1),
                "read-only",
            ),
            (
                "pull request target",
                original.replace("pull_request:", "pull_request_target:", 1),
                "only pull_request and push",
            ),
            (
                "moving Python",
                original.replace(
                    'python-version: "3.14.7"',
                    'python-version: "3.14"',
                    1,
                ),
                "exact Python 3.14.7",
            ),
            (
                "secret expression",
                original.replace(
                    "permissions:\n",
                    "env:\n  FIXTURE: ${{ secrets.FIXTURE }}\n\npermissions:\n",
                    1,
                ),
                "forbidden pull-request surface",
            ),
        )
        for name, mutated, owned_reason in scenarios:
            with self.subTest(name=name):
                self.assertNotEqual(original, mutated)
                failures = []
                check_unit_test_workflow_text(mutated, failures)
                self.assertTrue(
                    any(owned_reason in failure for failure in failures),
                    failures,
                )

    def test_action_graph_mutations_are_rejected(self):
        failures = []
        count = check_action_graph_fixtures(failures)
        self.assertEqual(7, count)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
