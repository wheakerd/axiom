"""Focused tests for release workflow and mutation policy."""

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.release_policy import check_release_signature_workflow_contract
from axiom_validation.cases.release_policy import check_release_script_runtime_contract
from axiom_validation.release_tag_controller import check_controller_workflow_contract


class ReleasePolicyTests(unittest.TestCase):
    def test_checked_in_release_workflow_and_mutations(self):
        failures = []
        workflow = check_release_signature_workflow_contract(failures)
        self.assertIsNotNone(workflow)
        count = check_release_script_runtime_contract(workflow, failures)
        self.assertEqual(55, count)
        self.assertEqual([], failures)

    def test_release_workflow_rejects_moving_runner(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workflows = root / ".github" / "workflows"
            shutil.copytree(REPOSITORY_ROOT / ".github" / "workflows", workflows)
            path = workflows / "release-signature-guard.yml"
            original = path.read_text(encoding="utf-8")
            mutated = original.replace("runs-on: ubuntu-24.04", "runs-on: ubuntu-latest", 1)
            self.assertNotEqual(original, mutated)
            path.write_text(mutated, encoding="utf-8")
            failures = []
            with mock.patch("axiom_validation.release_policy.REPOSITORY_ROOT", root):
                check_release_signature_workflow_contract(failures)
            self.assertEqual([f"{path} must use the fixed ubuntu-24.04 runner"], failures)

    def test_checked_in_release_tag_controller_workflow(self):
        failures = []
        check_controller_workflow_contract(failures)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
