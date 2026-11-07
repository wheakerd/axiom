"""Focused tests for repository layout and safety-domain gates."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from axiom_validation.context import RELEASE_VERSION, REPOSITORY_ROOT
from axiom_validation.repository_policy import (
    CRITICAL_CODEOWNER_PATTERNS,
    check_critical_path_owners,
    check_packaged_skills,
    check_release_version_surfaces,
    check_repository_governance_contract,
    check_required_files,
    check_skill_contracts,
)


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
                [sys.executable, "-B", ".ci/scripts/check-publication.py"],
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

    def test_repository_governance_and_codeowners_contract(self):
        failures = []
        count = check_repository_governance_contract(failures)
        self.assertEqual(len(CRITICAL_CODEOWNER_PATTERNS), count)
        self.assertEqual([], failures)

    def test_changelog_requires_the_current_version_entry(self):
        failures = self._release_surface_failures(
            "CHANGELOG.md", f"## {RELEASE_VERSION} - ", "Unversioned"
        )
        self.assertIn(f"CHANGELOG.md has no entry heading for {RELEASE_VERSION}", failures)

    def test_codeowners_rejects_a_missing_sibling_owner(self):
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(encoding="utf-8")
        mutated = codeowners.replace("/.ci/ @wheakerd\n", "", 1)
        self.assertNotEqual(codeowners, mutated)

        failures = []
        count = check_critical_path_owners(mutated, failures)
        self.assertEqual(len(CRITICAL_CODEOWNER_PATTERNS) - 1, count)
        self.assertTrue(any("/.ci/" in failure for failure in failures), failures)

    def test_codeowners_rejects_a_later_owner_override(self):
        codeowners = (REPOSITORY_ROOT / ".github/CODEOWNERS").read_text(encoding="utf-8")

        failures = []
        count = check_critical_path_owners(f"{codeowners}* @unexpected-owner\n", failures)
        self.assertEqual(len(CRITICAL_CODEOWNER_PATTERNS), count)
        self.assertIn(
            ".github/CODEOWNERS must retain the exact ordered critical-path owner set",
            failures,
        )


if __name__ == "__main__":
    unittest.main()
