"""Focused tests for traceable-Git safety gates and fixtures."""

import unittest

from axiom_validation.git_contracts import safe_git_oid, safe_git_operand
from tests.fixtures.git_contracts import check_traceable_security_contracts


class GitContractTests(unittest.TestCase):
    def test_all_traceable_git_fixtures(self):
        failures = []
        count = check_traceable_security_contracts(failures)
        self.assertEqual(56, count)
        self.assertEqual([], failures)

    def test_oid_and_literal_operand_gates(self):
        self.assertTrue(safe_git_oid("a" * 40, "sha1"))
        self.assertFalse(safe_git_oid("0" * 40, "sha1"))
        self.assertTrue(safe_git_operand("ref", "refs/heads/main", True))
        self.assertFalse(safe_git_operand("remote", "--upload-pack=evil", True))


if __name__ == "__main__":
    unittest.main()
