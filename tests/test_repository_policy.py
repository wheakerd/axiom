"""Focused tests for repository layout and safety-domain gates."""

import unittest

from axiom_validation.context import CURRENT_RELEASE_NOTES, REPOSITORY_ROOT
from axiom_validation.repository_policy import (
    CRITICAL_CODEOWNER_PATTERNS,
    check_packaged_skills,
    check_release_version_surfaces,
    check_repository_governance_contract,
    check_repository_governance_documents,
    check_required_files,
    check_skill_contracts,
    discover_release_documents,
)
from tests.fixtures.external_action import check_external_action_scenarios
from tests.fixtures.rollback import check_reversible_safety_scenarios


class RepositoryPolicyTests(unittest.TestCase):
    def test_current_skill_inventory_references_and_release_surfaces(self):
        failures = []
        check_required_files(failures)
        check_packaged_skills(failures)
        check_skill_contracts(failures)
        check_release_version_surfaces(failures)
        self.assertEqual([], failures)

    def test_release_documents_are_discovered(self):
        documents = discover_release_documents()
        self.assertIn(CURRENT_RELEASE_NOTES, documents)
        self.assertEqual(tuple(sorted(documents)), documents)

    def test_repository_governance_and_codeowners_contract(self):
        failures = []
        count = check_repository_governance_contract(failures)
        self.assertEqual(len(CRITICAL_CODEOWNER_PATTERNS), count)
        self.assertEqual([], failures)

    def test_repository_governance_rejects_a_missing_sibling_owner(self):
        governance = (REPOSITORY_ROOT / "docs/repository-governance.md").read_text(
            encoding="utf-8"
        )
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(
            encoding="utf-8"
        )
        mutated = codeowners.replace("/axiom_validation/ @wheakerd\n", "", 1)
        self.assertNotEqual(codeowners, mutated)

        failures = []
        count = check_repository_governance_documents(
            governance, mutated, failures
        )
        self.assertEqual(len(CRITICAL_CODEOWNER_PATTERNS) - 1, count)
        self.assertTrue(
            any("/axiom_validation/" in failure for failure in failures),
            failures,
        )

    def test_repository_governance_rejects_a_later_owner_override(self):
        governance = (REPOSITORY_ROOT / "docs/repository-governance.md").read_text(
            encoding="utf-8"
        )
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(
            encoding="utf-8"
        )
        mutated = f"{codeowners}* @unexpected-owner\n"

        failures = []
        count = check_repository_governance_documents(
            governance, mutated, failures
        )
        self.assertEqual(len(CRITICAL_CODEOWNER_PATTERNS), count)
        self.assertIn(
            ".github/CODEOWNERS must retain the exact ordered critical-path owner set",
            failures,
        )

    def test_external_action_fixtures(self):
        failures = []
        self.assertEqual(155, check_external_action_scenarios(failures))
        self.assertEqual([], failures)

    def test_rollback_fixtures(self):
        failures = []
        self.assertEqual(127, check_reversible_safety_scenarios(failures))
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
