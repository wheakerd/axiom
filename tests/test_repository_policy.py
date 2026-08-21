"""Focused tests for repository layout and safety-domain gates."""

import unittest

from axiom_validation.context import CURRENT_RELEASE_NOTES
from axiom_validation.repository_policy import discover_release_documents
from tests.fixtures.external_action import check_external_action_scenarios
from tests.fixtures.rollback import check_reversible_safety_scenarios


class RepositoryPolicyTests(unittest.TestCase):
    def test_release_documents_are_discovered(self):
        documents = discover_release_documents()
        self.assertIn(CURRENT_RELEASE_NOTES, documents)
        self.assertEqual(tuple(sorted(documents)), documents)

    def test_external_action_fixtures(self):
        failures = []
        self.assertEqual(12, check_external_action_scenarios(failures))
        self.assertEqual([], failures)

    def test_rollback_fixtures(self):
        failures = []
        check_reversible_safety_scenarios(failures)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
