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
    INSTRUCTION_MAX_BYTES,
    ROUTING_GATE_MAX_BYTES,
    ROUTING_GATE_RELATIVE,
    SKILL_DESCRIPTION_MAX_CHARACTERS,
    check_critical_path_owners,
    check_critical_path_targets,
    check_instruction_file_sizes,
    check_packaged_skills,
    check_repository_governance_contract,
    check_required_files,
    check_routing_gate_size,
    check_skill_contracts,
    check_skill_description,
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

    def _instruction_files(self, root, sizes):
        for relative_path, size in sizes.items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"x" * size)

    def test_size_boundaries_keep_their_decided_values(self):
        self.assertEqual(16384, INSTRUCTION_MAX_BYTES)
        self.assertEqual(7372, ROUTING_GATE_MAX_BYTES)
        self.assertEqual(1024, SKILL_DESCRIPTION_MAX_CHARACTERS)

    def test_instruction_sizes_accept_files_below_the_on_demand_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._instruction_files(
                root,
                {
                    "plugin/skills/fixture/SKILL.md": INSTRUCTION_MAX_BYTES - 1,
                    "plugin/skills/fixture/references/detail.md": INSTRUCTION_MAX_BYTES - 1,
                },
            )

            failures = []
            check_instruction_file_sizes(failures, root)
            self.assertEqual([], failures)

    def test_instruction_sizes_reject_an_entry_file_and_a_reference_at_the_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._instruction_files(
                root,
                {
                    "plugin/skills/fixture/SKILL.md": INSTRUCTION_MAX_BYTES,
                    "plugin/skills/fixture/references/detail.md": INSTRUCTION_MAX_BYTES + 1,
                },
            )

            failures = []
            check_instruction_file_sizes(failures, root)
            self.assertEqual(
                [
                    "plugin/skills/fixture/SKILL.md is 16384 bytes; "
                    "instruction files must stay below 16384",
                    "plugin/skills/fixture/references/detail.md is 16385 bytes; "
                    "instruction files must stay below 16384",
                ],
                sorted(failures),
            )

    def test_routing_gate_size_accepts_the_ceiling_and_rejects_one_byte_more(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._instruction_files(root, {ROUTING_GATE_RELATIVE: ROUTING_GATE_MAX_BYTES})

            failures = []
            check_routing_gate_size(failures, root)
            self.assertEqual([], failures)

            self._instruction_files(root, {ROUTING_GATE_RELATIVE: ROUTING_GATE_MAX_BYTES + 1})
            check_routing_gate_size(failures, root)
            self.assertEqual(
                [
                    "plugin/skills/using-axiom/SKILL.md has 7373 bytes; "
                    "the routing gate must stay within 7372 bytes"
                ],
                failures,
            )

    def test_skill_description_accepts_the_limit_and_rejects_one_character_more(self):
        failures = []
        check_skill_description("fixture", "x" * SKILL_DESCRIPTION_MAX_CHARACTERS, failures)
        self.assertEqual([], failures)

        check_skill_description("fixture", "x" * (SKILL_DESCRIPTION_MAX_CHARACTERS + 1), failures)
        check_skill_description("fixture", "", failures)
        self.assertEqual(
            [
                "fixture description has 1025 characters; "
                "a skill description must contain at most 1024",
                "fixture description must be non-empty",
            ],
            failures,
        )

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
