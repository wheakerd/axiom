"""Focused tests for repository layout and safety-domain gates."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.repository_policy import (
    CRITICAL_CODEOWNER_PATTERNS,
    check_critical_path_owners,
    check_critical_path_targets,
    check_packaged_skills,
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

    def test_current_skill_inventory_and_required_files(self):
        failures = []
        check_required_files(failures)
        check_packaged_skills(failures)
        check_skill_contracts(failures)
        self.assertEqual([], failures)

    def test_repository_governance_and_codeowners_contract(self):
        failures = []
        count = check_repository_governance_contract(failures)
        self.assertEqual(len(CRITICAL_CODEOWNER_PATTERNS), count)
        self.assertEqual([], failures)

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

    def _critical_path_tree(self, root):
        for pattern in CRITICAL_CODEOWNER_PATTERNS:
            target = root / pattern.strip("/")
            if pattern.endswith("/"):
                target = target / "nested" / "file.txt"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x\n", encoding="utf-8")

    def test_codeowners_targets_accept_a_tree_with_every_critical_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._critical_path_tree(root)

            failures = []
            check_critical_path_targets(failures, root)
            self.assertEqual([], failures)

    def test_codeowners_targets_reject_a_missing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._critical_path_tree(root)
            (root / "SECURITY.md").unlink()

            failures = []
            check_critical_path_targets(failures, root)
            self.assertEqual(
                [".github/CODEOWNERS pattern '/SECURITY.md' matches no file in the repository"],
                failures,
            )

    def test_codeowners_targets_reject_a_directory_without_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._critical_path_tree(root)
            shutil.rmtree(root / "plugin" / "hooks" / "nested")
            self.assertTrue((root / "plugin" / "hooks").is_dir())

            failures = []
            check_critical_path_targets(failures, root)
            self.assertEqual(
                [".github/CODEOWNERS pattern '/plugin/hooks/' matches no file in the repository"],
                failures,
            )


if __name__ == "__main__":
    unittest.main()
