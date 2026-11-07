"""Focused tests for the installed-runtime digest generator."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.release import stamp_manifest
from axiom_validation.runtime_identity import (
    INPUT_MANIFEST_RELATIVE,
    check_runtime_identity,
    compute_runtime_contract,
    load_json_document,
)



class RuntimeIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        failures: list[str] = []
        manifest = load_json_document(
            REPOSITORY_ROOT / INPUT_MANIFEST_RELATIVE,
            failures,
        )
        if manifest is None or failures:
            raise AssertionError(failures)
        cls.manifest = manifest
        contract = compute_runtime_contract(REPOSITORY_ROOT, manifest, failures)
        if contract is None or failures:
            raise AssertionError(failures)
        cls.expected_record_count = contract.record_count

    def copy_installed_surfaces(self, target: Path) -> None:
        for relative in self.manifest["installedSurfaceRoots"]:
            source = REPOSITORY_ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, destination, symlinks=True)
            else:
                shutil.copy2(source, destination)

    def copy_input_fixture(self, target: Path) -> None:
        self.copy_installed_surfaces(target)
        destination = target / INPUT_MANIFEST_RELATIVE
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY_ROOT / INPUT_MANIFEST_RELATIVE, destination)

    def compute(self, root: Path, manifest: dict | None = None):
        failures: list[str] = []
        result = compute_runtime_contract(root, manifest or self.manifest, failures)
        return result, failures

    def test_checked_in_input_policy_classifies_every_installed_file(self):
        failures: list[str] = []
        record_count = check_runtime_identity(failures)
        self.assertEqual(self.expected_record_count, record_count)
        self.assertGreater(record_count, 0)
        self.assertEqual([], failures)

    def test_stamping_the_release_version_leaves_the_digest_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.copy_installed_surfaces(root)
            for relative in ("plugin/.codex-plugin/plugin.json", "plugin/.claude-plugin/plugin.json"):
                path = root / relative
                document = json.loads(path.read_text(encoding="utf-8"))
                document.pop("version", None)
                path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            versionless, failures = self.compute(root)
            self.assertEqual([], failures)
            for relative in ("plugin/.codex-plugin/plugin.json", "plugin/.claude-plugin/plugin.json"):
                path = root / relative
                path.write_bytes(stamp_manifest(path.read_bytes(), "1.2.3", relative))
            stamped, stamped_failures = self.compute(root)
            self.assertEqual([], stamped_failures)
            self.assertEqual(versionless.digest, stamped.digest)

    def test_each_installed_behavior_class_changes_the_digest(self):
        mutations = {
            "skill": lambda root: self.append_text(
                root / "plugin/skills/agents-architect/SKILL.md", "\nChanged skill contract.\n"
            ),
            "hook": lambda root: self.append_text(
                root / "plugin/hooks/codex-hooks.json", "\n"
            ),
            "wrapper": lambda root: self.append_text(
                root / "plugin/hooks/codex-session-start.cmd", "\nrem changed wrapper\n"
            ),
            "route-boundary": lambda root: self.append_text(
                root / "plugin/skills/using-axiom/SKILL.md", "\nChanged route boundary.\n"
            ),
            "manifest-field": self.change_manifest_behavior,
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self.copy_installed_surfaces(root)
                baseline, baseline_failures = self.compute(root)
                self.assertEqual([], baseline_failures)
                self.assertIsNotNone(baseline)
                mutate(root)
                changed, changed_failures = self.compute(root)
                self.assertEqual([], changed_failures)
                self.assertIsNotNone(changed)
                self.assertNotEqual(baseline.digest, changed.digest)

    def test_repository_only_change_leaves_digest_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.copy_installed_surfaces(root)
            baseline, failures = self.compute(root)
            self.assertEqual([], failures)
            workflow = root / ".github/workflows/repository-only.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("name: repository-only\n", encoding="utf-8")
            current, current_failures = self.compute(root)
            self.assertEqual([], current_failures)
            self.assertEqual(baseline.digest, current.digest)

    def test_line_endings_are_canonical_across_operating_systems(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.copy_installed_surfaces(root)
            baseline, failures = self.compute(root)
            self.assertEqual([], failures)
            path = root / "plugin/skills/using-axiom/SKILL.md"
            text = path.read_text(encoding="utf-8")
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
            windows_checkout, windows_failures = self.compute(root)
            self.assertEqual([], windows_failures)
            self.assertEqual(baseline.digest, windows_checkout.digest)

    def test_input_policy_is_stable_for_crlf_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.copy_input_fixture(root)
            manifest_path = root / INPUT_MANIFEST_RELATIVE
            manifest_text = manifest_path.read_text(encoding="utf-8")
            manifest_path.write_bytes(manifest_text.replace("\n", "\r\n").encode("utf-8"))

            failures: list[str] = []
            record_count = check_runtime_identity(failures, root=root)
            self.assertEqual(self.expected_record_count, record_count)
            self.assertEqual([], failures)

    def test_missing_duplicate_unordered_escaping_symlink_and_unclassified_inputs_fail(self):
        fixtures = (
            ("missing", self.remove_hook_tree, "cannot inspect plugin/hooks"),
            ("duplicate", self.duplicate_input, "inputs paths must be unique"),
            ("unordered", self.reverse_inputs, "inputs must be ordered by path"),
            ("escaping", self.escape_input, "traversal segments"),
            ("symlink", self.symlink_input, "must not be a symbolic link"),
            ("dot-path", self.dot_input, "traversal segments"),
            ("unclassified", self.add_unclassified_surface, "surfaces are unclassified"),
        )
        for label, mutate, expected in fixtures:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self.copy_installed_surfaces(root)
                manifest = copy.deepcopy(self.manifest)
                mutate(root, manifest)
                result, failures = self.compute(root, manifest)
                self.assertIsNone(result)
                self.assertTrue(
                    any(expected in failure for failure in failures),
                    failures,
                )

    @staticmethod
    def append_text(path: Path, suffix: str) -> None:
        path.write_text(path.read_text(encoding="utf-8") + suffix, encoding="utf-8")

    @staticmethod
    def change_manifest_behavior(root: Path) -> None:
        path = root / "plugin/.codex-plugin/plugin.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["interface"]["defaultPrompt"][0] += " Review runtime identity."
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def remove_hook_tree(root: Path, manifest: dict) -> None:
        del manifest
        shutil.rmtree(root / "plugin" / "hooks")

    @staticmethod
    def duplicate_input(root: Path, manifest: dict) -> None:
        del root
        manifest["inputs"].insert(1, copy.deepcopy(manifest["inputs"][0]))

    @staticmethod
    def reverse_inputs(root: Path, manifest: dict) -> None:
        del root
        manifest["inputs"].reverse()

    @staticmethod
    def escape_input(root: Path, manifest: dict) -> None:
        del root
        manifest["inputs"][0]["path"] = "../outside.json"

    @staticmethod
    def symlink_input(root: Path, manifest: dict) -> None:
        del manifest
        path = root / "plugin/skills/using-axiom/SKILL.md"
        target = root / "outside-skill.md"
        target.write_text("outside\n", encoding="utf-8")
        path.unlink()
        path.symlink_to(target)

    @staticmethod
    def dot_input(root: Path, manifest: dict) -> None:
        del root
        manifest["inputs"][0]["path"] = "."

    @staticmethod
    def add_unclassified_surface(root: Path, manifest: dict) -> None:
        del manifest
        (root / "plugin/.codex-plugin/unclassified.json").write_text("{}\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
