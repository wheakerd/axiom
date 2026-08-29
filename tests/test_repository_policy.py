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
from axiom_validation.cases.external_action import check_external_action_scenarios
from axiom_validation.cases.rollback import check_reversible_safety_scenarios


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

    def test_repository_governance_rejects_stale_release_tag_creator_claim(self):
        governance = (REPOSITORY_ROOT / "docs/repository-governance.md").read_text(
            encoding="utf-8"
        )
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(
            encoding="utf-8"
        )
        mutated = governance.replace(
            "Release-tag creator allowlist: **GitHub App "
            "`axiom-release-tag-controller` only**",
            "Release-tag creator allowlist: **UNAVAILABLE**",
            1,
        )
        self.assertNotEqual(governance, mutated)

        failures = []
        check_repository_governance_documents(mutated, codeowners, failures)
        self.assertTrue(
            any(
                "retains stale governance claim" in failure
                and "Release-tag creator allowlist" in failure
                for failure in failures
            ),
            failures,
        )

    def test_repository_governance_rejects_contradictory_creation_ruleset(self):
        governance = (REPOSITORY_ROOT / "docs/repository-governance.md").read_text(
            encoding="utf-8"
        )
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(
            encoding="utf-8"
        )
        start = governance.index(
            "The separate active ruleset `restrict-release-tag-creation`"
        )
        end = governance.index("\n\nTogether,", start)
        contradictory = (
            "The separate inactive ruleset `restrict-release-tag-creation` "
            "historically targeted exactly `refs/tags/v*`. It contains no "
            "`creation` rule. An old response recorded `actor_id: 78034820`, "
            "`actor_type: User`, `bypass_mode: always`, and "
            "`current_user_can_bypass: always`. Because this is historical, the "
            "current bypass scope is unknown.\n"
        )
        mutated = governance[:start] + contradictory + governance[end:]

        failures = []
        check_repository_governance_documents(mutated, codeowners, failures)
        self.assertTrue(
            any("Release Tag Policy is missing scoped anchor" in failure for failure in failures),
            failures,
        )

    def test_repository_governance_rejects_review_boundary_claim_drift(self):
        governance = (REPOSITORY_ROOT / "docs/repository-governance.md").read_text(
            encoding="utf-8"
        )
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(
            encoding="utf-8"
        )
        transition = (
            "That test must prove that the approval counts without author "
            "self-approval or a\nruleset bypass."
        )
        hardware_limit = (
            "Hardware-backed\nauthentication and an independently controlled release "
            "identity were not\nverified by the repository or API evidence used for "
            "this snapshot and are not\nclaimed as current compensating controls."
        )
        audit_limit = (
            "Emergency or administrative ruleset changes remain separately "
            "auditable\nthrough GitHub's ruleset version history. Every currently "
            "observed history\nentry identifies `actor_id: 78034820` and "
            "`actor_type: User`, which maps to the\nsame `wheakerd` identity. That "
            "audit trail is detective evidence; because the\ngoverning administrator "
            "remains the same identity, it does not constitute an\nindependent trust "
            "domain."
        )
        fixtures = (
            (
                "deleted transition condition",
                governance.replace(transition, "", 1),
                "missing scoped anchor",
            ),
            (
                "reversed selected path",
                governance.replace(
                    "`Path B: document the single-maintainer trust boundary` is the "
                    "selected policy",
                    "`Path A: enforce independent review` is the selected policy",
                    1,
                ),
                "unsupported review-boundary claim",
            ),
            (
                "exaggerated authentication and release controls",
                governance.replace(
                    hardware_limit,
                    hardware_limit
                    + "\n\nHardware-backed authentication and an independently "
                    "controlled release identity are verified current compensating "
                    "controls.",
                    1,
                ),
                "unsupported review-boundary claim",
            ),
            (
                "exaggerated ruleset audit independence",
                governance.replace(
                    audit_limit,
                    audit_limit
                    + "\n\nRuleset history constitutes an independent trust domain.",
                    1,
                ),
                "unsupported review-boundary claim",
            ),
            (
                "exaggerated code-owner enforcement",
                governance
                + "\n\nCODEOWNERS blocks an unapproved merge.\n",
                "unsupported review-boundary claim",
            ),
        )

        for label, mutated, expected_failure in fixtures:
            with self.subTest(label=label):
                self.assertNotEqual(governance, mutated)
                failures = []
                check_repository_governance_documents(
                    mutated, codeowners, failures
                )
                self.assertTrue(
                    any(expected_failure in failure for failure in failures),
                    failures,
                )

    def test_repository_governance_rejects_controller_permission_drift(self):
        governance = (REPOSITORY_ROOT / "docs/repository-governance.md").read_text(
            encoding="utf-8"
        )
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(
            encoding="utf-8"
        )
        mutated = governance.replace(
            "only `administration: read` plus `contents: write`; administration write is not\n"
            "granted.",
            "`administration: write` and `contents: write`.",
            1,
        )
        self.assertNotEqual(governance, mutated)

        failures = []
        check_repository_governance_documents(mutated, codeowners, failures)
        self.assertTrue(
            any("Release Tag Controller Migration" in failure for failure in failures),
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
