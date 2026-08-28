"""Focused tests for release workflow and mutation policy."""

import unittest

from axiom_validation.release_policy import check_release_signature_workflow_contract
from axiom_validation.cases.release_policy import check_release_script_runtime_contract


class ReleasePolicyTests(unittest.TestCase):
    def test_checked_in_release_workflow_and_mutations(self):
        failures = []
        workflow = check_release_signature_workflow_contract(failures)
        self.assertIsNotNone(workflow)
        count = check_release_script_runtime_contract(workflow, failures)
        self.assertEqual(54, count)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
