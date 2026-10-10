"""Focused tests for repository layout and safety-domain gates."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from axiom_validation.context import CURRENT_RELEASE_NOTES, RELEASE_VERSION, REPOSITORY_ROOT
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
    def test_publication_command_preserves_source_tree_without_bytecode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "axiom"
            shutil.copytree(
                REPOSITORY_ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            result = subprocess.run(
                [sys.executable, "-B", "scripts/check-publication.py"],
                cwd=root,
                env=environment,
                text=True,
                capture_output=True,
                timeout=120,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("Publication validation passed:", result.stdout)
            self.assertEqual([], list(root.rglob("__pycache__")))
            self.assertEqual([], list(root.rglob("*.pyc")))

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

    def _release_surface_failures(self, relative, old, new):
        target = REPOSITORY_ROOT / relative
        original_read = Path.read_text
        original = original_read(target, encoding="utf-8")
        self.assertIn(old, original)

        def read_changed(path, *args, **kwargs):
            text = original_read(path, *args, **kwargs)
            return text.replace(old, new) if path == target else text

        failures = []
        with patch.object(Path, "read_text", read_changed):
            check_release_version_surfaces(failures)
        return failures

    def test_current_guides_require_canonical_sources_even_with_version_prose(self):
        for relative, anchor in (
            ("README.md", "](evidence/release-status.json)"),
            ("README.md", "](docs/compatibility.md)"),
            ("README.md", "](CHANGELOG.md)"),
            ("docs/compatibility.md", "](../evidence/release-status.json)"),
            ("docs/compatibility.md", "](../evidence/runtime-identity.json)"),
        ):
            with self.subTest(relative=relative, anchor=anchor):
                # Repeating the version and old release-note link cannot
                # replace the current source owner.
                legacy_prose = (
                    "](missing.json)\n"
                    f"The checked-in candidate for `v{RELEASE_VERSION}` reports:\n"
                    f"[Notes](docs/releases/v{RELEASE_VERSION}.md)\n"
                    f"[Notes](releases/v{RELEASE_VERSION}.md)\n"
                )
                failures = self._release_surface_failures(relative, anchor, legacy_prose)
                self.assertTrue(
                    any(relative in failure and repr(anchor) in failure for failure in failures),
                    failures,
                )

    def test_release_history_still_requires_the_exact_candidate_version(self):
        for relative, anchor in (
            ("CHANGELOG.md", f"## {RELEASE_VERSION} - "),
            (CURRENT_RELEASE_NOTES, f"Version `{RELEASE_VERSION}`"),
        ):
            with self.subTest(relative=relative):
                failures = self._release_surface_failures(relative, anchor, "Unversioned")
                self.assertTrue(
                    any(relative in failure and repr(anchor) in failure for failure in failures),
                    failures,
                )

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

    def test_repository_governance_rejects_required_guard_environment_drift(self):
        governance = (REPOSITORY_ROOT / "docs/repository-governance.md").read_text(
            encoding="utf-8"
        )
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(
            encoding="utf-8"
        )
        mutated = governance.replace(
            "exact `ubuntu-24.04` runner",
            "moving `ubuntu-latest` runner",
            1,
        )
        self.assertNotEqual(governance, mutated)

        failures = []
        check_repository_governance_documents(mutated, codeowners, failures)
        self.assertTrue(
            any(
                "Repository Guards Canonical Environment" in failure
                and "ubuntu-24.04" in failure
                for failure in failures
            ),
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
                "stale required-check count",
                governance.replace(
                    "Server-side enforcement of the three required check contexts",
                    "Server-side enforcement of the two required check contexts",
                    1,
                ),
                "unsupported review-boundary claim",
            ),
            (
                "contradictory required-check summary",
                governance + "\n\n`repository-guards` and "
                "`unit-and-integration-tests` remain the only required checks.\n",
                "unsupported review-boundary claim",
            ),
            (
                "demoted hook aggregate",
                governance.replace(
                    "The three native\nhook-runtime matrix jobs supply the required "
                    "aggregate; they are not separate\nrequired check contexts.",
                    "The three hook-runtime matrix checks plus `hook-runtime-gate` "
                    "remain non-required review evidence.",
                    1,
                ),
                "unsupported review-boundary claim",
            ),
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

    def test_repository_governance_rejects_weakened_hook_runtime_promotion(self):
        governance = (REPOSITORY_ROOT / "docs/repository-governance.md").read_text(
            encoding="utf-8"
        )
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(
            encoding="utf-8"
        )
        mutated = governance.replace(
            "at least 30 consecutive completed `push` runs on `main`",
            "at least 3 consecutive completed `push` runs on `main`",
            1,
        )
        self.assertNotEqual(governance, mutated)

        failures = []
        check_repository_governance_documents(mutated, codeowners, failures)
        self.assertTrue(
            any(
                "Hook Runtime Promotion Gate" in failure
                and "30 consecutive" in failure
                for failure in failures
            ),
            failures,
        )

    def test_repository_governance_requires_promoted_aggregate_evidence(self):
        governance = (REPOSITORY_ROOT / "docs/repository-governance.md").read_text(
            encoding="utf-8"
        )
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(
            encoding="utf-8"
        )
        for anchor in (
            "`hook-runtime-gate` is required",
            "The observation gate is **SATISFIED**",
            "Fork execution remains\n**NOT-RUN**",
            "The release-tag controller now requires the same three exact main checks",
        ):
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, governance)
                failures = []
                check_repository_governance_documents(
                    governance.replace(anchor, "REMOVED", 1), codeowners, failures
                )
                self.assertTrue(
                    any("Hook Runtime Promotion Gate" in failure for failure in failures),
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
